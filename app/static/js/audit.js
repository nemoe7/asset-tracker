(() => {
  const filterButton = document.getElementById('audit-filter-button');

  if (filterButton) {
    filterButton.addEventListener('click', () => {
      openModal(document.getElementById('filter-audit-modal'));
    });
  }

  const sentinel = document.getElementById('audit-sentinel');
  const counter = document.getElementById('audit-count');
  const loadMore = document.getElementById('audit-load-more');
  const desktopBody = document.getElementById('audit-rows-desktop');
  const mobileList = document.getElementById('audit-rows-mobile');

  if (!counter || !desktopBody || !mobileList) return;

  const total = Number.parseInt(counter.dataset.total, 10) || 0;
  let shown = Number.parseInt(counter.dataset.shown, 10) || 0;
  let nextPage = sentinel ? Number.parseInt(sentinel.dataset.nextPage, 10) || 2 : 2;
  let hasMore = sentinel ? sentinel.dataset.hasMore === 'true' : false;
  let loading = false;

  if (loadMore) {
    loadMore.hidden = true;
  }

  const updateCounter = () => {
    counter.textContent = `Showing ${shown} of ${total} events`;
  };

  const finish = () => {
    const parent = sentinel ? sentinel.parentElement : loadMore ? loadMore.parentElement : null;

    if (sentinel) sentinel.remove();
    if (loadMore) loadMore.remove();

    if (parent && !document.getElementById('audit-end')) {
      const end = document.createElement('p');
      end.id = 'audit-end';
      end.className = 'text-sm text-zinc-500';
      end.textContent = `End of activity · ${total} events`;
      parent.appendChild(end);
    }

    hasMore = false;
  };

  const formatAuditTimestamps = () => {
    for (const node of document.querySelectorAll('[data-audit-timestamp]')) {
      const utc = node.dataset.utc;
      const date = utc ? new Date(utc.replace(' ', 'T') + 'Z') : null;

      if (date && !Number.isNaN(date.getTime())) {
        node.textContent = date.toLocaleString();
      }
    }
  };

  const appendChunk = (chunk) => {
    for (const template of chunk.querySelectorAll('template')) {
      const target = document.getElementById(template.dataset.target);

      if (target) {
        target.appendChild(template.content.cloneNode(true));
      }
    }

    shown = document.querySelectorAll('#audit-rows-desktop [data-audit-row]').length;
    updateCounter();
    formatAuditTimestamps();
  };

  formatAuditTimestamps();

  const loadChunk = async () => {
    if (loading || !hasMore) return;

    loading = true;

    const params = new URLSearchParams(window.location.search);
    params.set('page', String(nextPage));

    try {
      const response = await fetch(`/admin/audit/fragment?${params.toString()}`);

      if (!response.ok) throw new Error('Failed to load activity');

      const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
      const chunk = doc.getElementById('audit-chunk');

      if (!chunk) throw new Error('Malformed activity fragment');

      appendChunk(chunk);

      hasMore = chunk.dataset.hasMore === 'true';
      nextPage = Number.parseInt(chunk.dataset.nextPage, 10) || nextPage + 1;

      if (!hasMore) finish();
    } catch (error) {
      hasMore = false;
      if (sentinel) sentinel.remove();
      if (loadMore) loadMore.hidden = false;
    } finally {
      loading = false;
    }
  };

  if (sentinel && hasMore) {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) loadChunk();
      },
      { rootMargin: '400px 0px' },
    );

    observer.observe(sentinel);
  }
})();
