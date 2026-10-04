(() => {
  const buttons = [...document.querySelectorAll('[data-category]')];
  const groups = [...document.querySelectorAll('[data-group]')];
  const search = document.getElementById('search');
  const sort = document.getElementById('sort');
  let category = 'all';
  function render() {
    const normalize = value => value.toLowerCase().replace(/[^a-z0-9]/g, '');
    const query = normalize(search.value);
    let count = 0;
    for (const group of groups) {
      const rows = [...group.querySelectorAll('.provider-row')];
      rows.sort((a, b) => sort.value === 'name'
        ? a.dataset.name.localeCompare(b.dataset.name)
        : Number(b.dataset[sort.value]) - Number(a.dataset[sort.value]) || a.dataset.name.localeCompare(b.dataset.name));
      let matches = 0;
      for (const row of rows) {
        row.hidden = !(normalize(row.dataset.search).includes(query) && (category === 'all' || category === group.dataset.group));
        if (!row.hidden) matches++;
        group.querySelector('.rows').append(row);
      }
      group.hidden = matches === 0;
      count += matches;
    }
    document.getElementById('result-count').textContent = `Showing ${count} provider${count === 1 ? '' : 's'}`;
    document.getElementById('empty').hidden = count !== 0;
  }
  for (const button of buttons) button.addEventListener('click', () => {
    category = button.dataset.category;
    for (const item of buttons) {
      item.classList.toggle('active', item === button);
      item.setAttribute('aria-pressed', String(item === button));
    }
    render();
  });
  document.getElementById('crypto-shortcut').addEventListener('click', () => {
    search.value = '';
    buttons.find(button => button.dataset.category === 'crypto').click();
  });
  search.addEventListener('input', render);
  sort.addEventListener('change', render);
  render();
})();
