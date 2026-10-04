(() => {
  const buttons = [...document.querySelectorAll('[data-category]')];
  const groups = [...document.querySelectorAll('[data-group]')];
  const search = document.getElementById('search');
  const sort = document.getElementById('sort');
  const coverage = document.getElementById('coverage');
  const minimum = document.getElementById('minimum');
  const reset = document.getElementById('reset');
  const params = new URLSearchParams(location.search);
  let category = ['all', 'cash', 'crypto'].includes(params.get('category')) ? params.get('category') : 'all';
  search.value = params.get('q') || '';
  for (const [control, key] of [[sort, 'sort'], [coverage, 'coverage'], [minimum, 'min']]) {
    if ([...control.options].some(option => option.value === params.get(key))) control.value = params.get(key);
  }
  function render() {
    const normalize = value => value.toLowerCase().replace(/[^a-z0-9]/g, '');
    const query = normalize(search.value);
    const ascending = sort.value.endsWith('-asc');
    const field = sort.value.replace('-asc', '');
    for (const button of document.querySelectorAll('[data-sort]')) {
      const active = button.dataset.sort === field;
      const label = button.dataset.sort === 'base' ? 'Base APY' : 'Top APY';
      button.textContent = `${label.toUpperCase()} ${active ? (ascending ? '↑' : '↓') : '↕'}`;
      button.setAttribute('aria-pressed', String(active));
      button.setAttribute('aria-label', `${label}: ${active ? (ascending ? 'sorted low to high; sort high to low' : 'sorted high to low; sort low to high') : 'sort high to low'}`);
    }
    let count = 0;
    for (const button of buttons) {
      const active = button.dataset.category === category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    }
    for (const group of groups) {
      const rows = [...group.querySelectorAll('.provider-row')];
      rows.sort((a, b) => {
        const byName = a.dataset.name.localeCompare(b.dataset.name);
        if (field === 'name') return byName;
        const av = Number(a.dataset[field]), bv = Number(b.dataset[field]);
        // Missing APYs stay last in either direction.
        if (av < 0 || bv < 0) return av < 0 && bv < 0 ? byName : av < 0 ? 1 : -1;
        return (ascending ? av - bv : bv - av) || byName;
      });
      let matches = 0;
      for (const row of rows) {
        row.hidden = !(normalize(row.dataset.search).includes(query)
          && (category === 'all' || category === group.dataset.group)
          && (coverage.value === 'all' || coverage.value === row.dataset.fdic)
          && Number(row.dataset.top) >= Number(minimum.value));
        if (!row.hidden) matches++;
        group.querySelector('.rows').append(row);
      }
      group.hidden = matches === 0;
      count += matches;
    }
    const total = document.querySelectorAll('.provider-row').length;
    document.getElementById('result-count').textContent = `${count} of ${total} providers`;
    document.getElementById('empty').hidden = count !== 0;
    reset.disabled = !search.value && category === 'all' && coverage.value === 'all' && minimum.value === '0' && sort.value === 'top';
    const url = new URL(location.href);
    for (const [key, value, fallback] of [['q', search.value, ''], ['category', category, 'all'], ['coverage', coverage.value, 'all'], ['min', minimum.value, '0'], ['sort', sort.value, 'top']]) {
      if (value === fallback) url.searchParams.delete(key);
      else url.searchParams.set(key, value);
    }
    history.replaceState(null, '', url);
  }
  for (const button of buttons) button.addEventListener('click', () => { category = button.dataset.category; render(); });
  for (const button of document.querySelectorAll('[data-sort]')) button.addEventListener('click', () => {
    sort.value = sort.value === button.dataset.sort ? `${button.dataset.sort}-asc` : button.dataset.sort;
    render();
  });
  search.addEventListener('input', render);
  for (const control of [sort, coverage, minimum]) control.addEventListener('change', render);
  reset.addEventListener('click', () => {
    category = 'all'; search.value = ''; coverage.value = 'all'; minimum.value = '0'; sort.value = 'top'; render();
  });
  render();
})();
