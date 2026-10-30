(function () {
  try {
    const theme = localStorage.getItem('yanrh-theme');
    if (theme === 'light') document.documentElement.dataset.theme = 'light';
  } catch (_) {}
  document.addEventListener('DOMContentLoaded', function () {
    const theme = document.querySelector('.theme-toggle');
    if (theme) {
      theme.hidden = false;
      function label() {
        const light = document.documentElement.dataset.theme === 'light';
        theme.textContent = light ? '☀' : '☾';
        theme.setAttribute('aria-label', light ? '切换到深色主题' : '切换到浅色主题');
        theme.title = theme.getAttribute('aria-label');
      }
      label();
      theme.addEventListener('click', function () {
        const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
        document.documentElement.dataset.theme = next;
        try { localStorage.setItem('yanrh-theme', next); } catch (_) {}
        label();
      });
    }
    const sort = document.querySelector('.sort-toggle');
    const list = document.getElementById('entries');
    if (sort && list && list.children.length > 1) {
      sort.hidden = false;
      let oldest = false;
      sort.addEventListener('click', function () {
        Array.from(list.children).reverse().forEach(item => list.appendChild(item));
        oldest = !oldest;
        sort.textContent = oldest ? '时间 ↑' : '时间 ↓';
        sort.setAttribute('aria-label', oldest ? '按时间倒序排列' : '按时间正序排列');
      });
    }
  });
})();

