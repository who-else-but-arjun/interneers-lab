const LOW_STOCK = 5;
let nextId = 16;
let filtersOpen = true;
let selectedCats = [];
let selectedBrands = [];
let priceMin = '';
let priceMax = '';
let qtyMin = '';
let qtyMax = '';
let showAllCats = false;
let showAllBrands = false;
let chartInstance = null;
let currentChart = 'stock';
let currentPage = 1;
let pageSize = 5;

async function loadProducts() {
  try {
    const response = await fetch('/products/?page_size=100');
    const data = await response.json();
    products = data.items.map(item => ({
      id: item.id,
      name: item.name,
      brand: item.brand,
      category: item.category,
      description: item.description,
      price: item.price,
      quantity: item.quantity,
      policy: item.policy || {
        warranty_period: '',
        return_window: '',
        refund_policy: '',
        vendor_faq_link: ''
      }
    }));
    render();
  } catch (e) {
    console.error('Failed to load products', e);
  }
}

function getFiltered() {
  const s = document.getElementById('searchInput').value.toLowerCase();
  let list = products;
  if (s) list = list.filter(p => p.name.toLowerCase().includes(s) || p.brand.toLowerCase().includes(s) || p.category.toLowerCase().includes(s));
  if (selectedCats.length) list = list.filter(p => selectedCats.includes(p.category));
  if (selectedBrands.length) list = list.filter(p => selectedBrands.includes(p.brand));
  
  // Price range filter
  if (priceMin !== '') list = list.filter(p => p.price >= parseFloat(priceMin));
  if (priceMax !== '') list = list.filter(p => p.price <= parseFloat(priceMax));
  
  // Quantity range filter
  if (qtyMin !== '') list = list.filter(p => p.quantity >= parseInt(qtyMin));
  if (qtyMax !== '') list = list.filter(p => p.quantity <= parseInt(qtyMax));
  
  return list;
}

function getCats() { return [...new Set(products.map(p => p.category))].sort(); }
function getBrands() { return [...new Set(products.map(p => p.brand))].sort(); }
function fmt(n) { return n.toLocaleString('en-IN'); }

function toggleFilters() {
  filtersOpen = !filtersOpen;
  document.getElementById('filterBody').style.display = filtersOpen ? '' : 'none';
  document.getElementById('filterChevron').innerHTML = filtersOpen
    ? '<polyline points="18 15 12 9 6 15"/>'
    : '<polyline points="6 9 12 15 18 9"/>';
}

function render() {
  const allFiltered = getFiltered();
  const totalItems = allFiltered.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  if (currentPage > totalPages) currentPage = totalPages || 1;
  const start = (currentPage - 1) * pageSize;
  const paginated = allFiltered.slice(start, start + pageSize);

  const lowStock = products.filter(p => p.quantity <= LOW_STOCK);

  const ab = document.getElementById('alertBanner');
  if (lowStock.length) {
    ab.innerHTML = `<div class="alert-banner"><div class="top-row"><span class="badge-pill">⚠ Stock Alert</span><span>${lowStock.length} product${lowStock.length>1?'s':''} at or below ${LOW_STOCK} units</span></div><div class="pills">${lowStock.map(p=>`<span class="pill">${p.name} (${p.quantity})</span>`).join('')}</div></div>`;
  } else { ab.innerHTML = ''; }

  const totalQty = products.reduce((s,p) => s+p.quantity, 0);
  const totalVal = products.reduce((s,p) => s+p.price*p.quantity, 0);
  document.getElementById('metrics').innerHTML = [
    {l:'Total Products',v:fmt(products.length)},
    {l:'Total Quantity',v:fmt(totalQty)},
    {l:'Inventory Value (₹)',v:'₹'+fmt(totalVal)}
  ].map(c => `<div class="card metric"><div class="metric-label">${c.l}</div><div class="metric-value">${c.v}</div></div>`).join('');

  document.getElementById('itemCount').textContent = totalItems + ' items';

  document.getElementById('tableWrap').innerHTML = `<table>
    <thead><tr><th style="width:40px"><input type="checkbox" onchange="toggleAllCheckboxes(this)" /></th><th style="width:32px"></th><th>Name</th><th>Brand</th><th>Category</th><th class="r">Price (₹)</th><th class="r">Qty</th><th>Actions</th></tr></thead>
    <tbody>${paginated.length === 0 ? '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--muted)">No products found</td></tr>' : paginated.map(p => {
      const hasPolicy = p.policy && (p.policy.warranty_period || p.policy.return_window || p.policy.refund_policy);
      const policyTooltip = hasPolicy ? `Warranty: ${p.policy.warranty_period || 'N/A'}\nReturn: ${p.policy.return_window || 'N/A'}\nRefund: ${p.policy.refund_policy || 'N/A'}` : 'No policy info';
      return `<tr>
      <td><input type="checkbox" class="row-cb" /></td>
      <td style="text-align:center;vertical-align:middle;">${hasPolicy ? `<button data-policy="${encodeURIComponent(policyTooltip)}" style="width:20px;height:20px;border-radius:50%;background:white;color:#5c2145;border:1.5px solid #5c2145;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(92,33,69,0.2);transition:all 0.2s;" title="View policy information" aria-label="View policy" onmouseenter="showPolicyTooltip(event)" onmouseleave="hidePolicyTooltip()" onmouseover="this.style.transform='scale(1.1)';this.style.background='#5c2145';this.style.color='white';" onmouseout="this.style.transform='scale(1)';this.style.background='white';this.style.color='#5c2145';">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" style="width:10px;height:10px;">
    <path fill-rule="evenodd" d="M10 1.944A11.954 11.954 0 012.166 5C2.056 5.649 2 6.319 2 7c0 5.225 3.34 9.67 8 11.317C14.66 16.67 18 12.225 18 7c0-.682-.057-1.35-.166-2.001A11.954 11.954 0 0110 1.944zm0 0v0zm0 0v0zM10 12a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
  </svg>
</button>` : ''}</td>
      <td style="position:relative;"><div class="prod-name" style="font-weight:600;color:#0f172a;">${p.name}</div><div class="prod-desc" style="font-size:11px;color:#64748b;margin-top:2px;line-height:1.3;">${p.description || ''}</div></td>
      <td style="color:var(--muted)">${p.brand}</td>
      <td style="white-space:nowrap;"><span class="cat-badge">${p.category}</span></td>
      <td class="r" style="font-weight:500">₹${fmt(p.price)}</td>
      <td class="r"><span class="${p.quantity<=LOW_STOCK?'qty-low':'qty-ok'}">${p.quantity}</span></td>
      <td><div style="display:flex;gap:8px;"><button onclick="findSimilarProducts('${p.id}')" style="padding:8px 14px;font-size:12px;font-weight:500;background:#fff;border:1.5px solid #5c2145;color:#5c2145;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:all 0.2s;height:36px;box-sizing:border-box;" onmouseover="this.style.background='#5c2145';this.style.color='#fff';this.style.transform='translateY(-1px)';" onmouseout="this.style.background='#fff';this.style.color='#5c2145';this.style.transform='translateY(0)';"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="21.17" y1="4.83" x2="16.66" y2="9.34"/><line x1="7.34" y1="14.66" x2="2.83" y2="19.17"/></svg>Similar</button><button onclick="removeProduct('${p.id}')" style="padding:8px 14px;font-size:12px;font-weight:500;background:#fff;border:1.5px solid #dc3545;color:#dc3545;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:all 0.2s;height:36px;box-sizing:border-box;" onmouseover="this.style.background='#dc3545';this.style.color='#fff';this.style.transform='translateY(-1px)';" onmouseout="this.style.background='#fff';this.style.color='#dc3545';this.style.transform='translateY(0)';"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;flex-shrink:0;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>Delete</button></div></td>
    </tr>`}).join('')}</tbody></table>`;

  renderPagination(totalPages);
  renderFilters();
  updateSemanticSearchCategories();
  renderCharts(allFiltered);
}

function renderPagination(totalPages) {
  if (totalPages <= 1) {
    document.getElementById('pagination').innerHTML = '';
    return;
  }
  let buttons = [];
  buttons.push(`<button class="btn btn-outline ${currentPage === 1 ? 'disabled' : ''}" onclick="${currentPage > 1 ? 'goToPage(' + (currentPage-1) + ')' : ''}">Prev</button>`);
  const start = Math.max(1, currentPage - 1);
  const end = Math.min(totalPages, currentPage + 1);
  for (let i = start; i <= end; i++) {
    buttons.push(`<button class="btn ${i === currentPage ? 'btn-primary' : 'btn-outline'}" onclick="goToPage(${i})">${i}</button>`);
  }
  buttons.push(`<button class="btn btn-outline ${currentPage === totalPages ? 'disabled' : ''}" onclick="${currentPage < totalPages ? 'goToPage(' + (currentPage+1) + ')' : ''}">Next</button>`);
  document.getElementById('pagination').innerHTML = `<div class="pagination">${buttons.join('')}</div>`;
}

function updateSemanticSearchCategories() {
  const cats = getCats();
  const select = document.getElementById('semanticSearchCategory');
  if (!select) return;
  const currentValue = select.value;
  select.innerHTML = '<option value="">All Categories</option>' + 
    cats.map(c => `<option value="${c}">${c}</option>`).join('');
  select.value = currentValue;
}

function goToPage(page) {
  currentPage = page;
  render();
}

function renderFilters() {
  const cats = getCats();
  const brands = getBrands();
  const MAX_VISIBLE = 5;
  
  const visibleCats = showAllCats ? cats : cats.slice(0, MAX_VISIBLE);
  const visibleBrands = showAllBrands ? brands : brands.slice(0, MAX_VISIBLE);
  
  // Calculate min/max for sliders
  const allProducts = products;
  const maxPrice = allProducts.length > 0 ? Math.max(...allProducts.map(p => p.price)) : 100000;
  const maxQty = allProducts.length > 0 ? Math.max(...allProducts.map(p => p.quantity)) : 1000;
  
  const priceMinVal = priceMin !== '' ? parseInt(priceMin) : 0;
  const priceMaxVal = priceMax !== '' ? parseInt(priceMax) : maxPrice;
  const qtyMinVal = qtyMin !== '' ? parseInt(qtyMin) : 0;
  const qtyMaxVal = qtyMax !== '' ? parseInt(qtyMax) : maxQty;
  
  document.getElementById('filterBody').innerHTML = `
    <div class="filter-section">
      <p style="font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;">Price Range (₹)</p>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
        <input type="number" id="priceMinInput" placeholder="Min" value="${priceMin}" oninput="updatePriceFilter('min', this.value)" style="width: 60px; padding:6px 8px; font-size:12px; border:1.5px solid #5c2145; border-radius:6px; outline:none;">
        <span style="color:#64748b;font-size:12px;">to</span>
        <input type="number" id="priceMaxInput" placeholder="Max" value="${priceMax}" oninput="updatePriceFilter('max', this.value)" style="width: 60px; padding:6px 8px; font-size:12px; border:1.5px solid #5c2145; border-radius:6px; outline:none;">
        <span style="font-size:11px;color:#64748b;">(Max: ₹${maxPrice.toLocaleString()})</span>
      </div>
      <div class="dual-slider-container" style="position:relative;height:28px;margin:8px 0;">
        <div class="dual-slider-track" style="position:absolute;top:50%;transform:translateY(-50%);width:100%;height:6px;background:#e2e8f0;border-radius:3px;"></div>
        <div class="dual-slider-fill" id="priceFill" style="position:absolute;top:50%;transform:translateY(-50%);height:6px;background:linear-gradient(135deg, #5c2145, #8b3a5c);border-radius:3px;left:${(parseInt(priceMin||0)/maxPrice)*100}%;width:${((parseInt(priceMax||maxPrice)-parseInt(priceMin||0))/maxPrice)*100}%;"></div>
        <div class="dual-slider-thumb" id="priceThumbMin" style="left:${(parseInt(priceMin||0)/maxPrice)*100}%;"></div>
        <div class="dual-slider-thumb" id="priceThumbMax" style="left:${(parseInt(priceMax||maxPrice)/maxPrice)*100}%;"></div>
        <input type="range" min="0" max="${maxPrice}" value="${priceMin||0}" class="dual-slider-input" style="z-index:2;" oninput="updateDualSlider('price', 'min', this.value, ${maxPrice})">
        <input type="range" min="0" max="${maxPrice}" value="${priceMax||maxPrice}" class="dual-slider-input" style="z-index:3;" oninput="updateDualSlider('price', 'max', this.value, ${maxPrice})">
      </div>
    </div>
    <div class="filter-section">
      <p style="font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;">Quantity Range</p>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
        <input type="number" id="qtyMinInput" placeholder="Min" value="${qtyMin}" oninput="updateQtyFilter('min', this.value)" style="width: 60px; padding:6px 8px; font-size:12px; border:1.5px solid #5c2145; border-radius:6px; outline:none;">
        <span style="color:#64748b;font-size:12px;">to</span>
        <input type="number" id="qtyMaxInput" placeholder="Max" value="${qtyMax}" oninput="updateQtyFilter('max', this.value)" style="width: 60px; padding:6px 8px; font-size:12px; border:1.5px solid #5c2145; border-radius:6px; outline:none;">
        <span style="font-size:11px;color:#64748b;">(Max: ${maxQty.toLocaleString()})</span>
      </div>
      <div class="dual-slider-container" style="position:relative;height:28px;margin:8px 0;">
        <div class="dual-slider-track" style="position:absolute;top:50%;transform:translateY(-50%);width:100%;height:6px;background:#e2e8f0;border-radius:3px;"></div>
        <div class="dual-slider-fill" id="qtyFill" style="position:absolute;top:50%;transform:translateY(-50%);height:6px;background:linear-gradient(135deg, #5c2145, #8b3a5c);border-radius:3px;left:${(parseInt(qtyMin||0)/maxQty)*100}%;width:${((parseInt(qtyMax||maxQty)-parseInt(qtyMin||0))/maxQty)*100}%;"></div>
        <div class="dual-slider-thumb" id="qtyThumbMin" style="left:${(parseInt(qtyMin||0)/maxQty)*100}%;"></div>
        <div class="dual-slider-thumb" id="qtyThumbMax" style="left:${(parseInt(qtyMax||maxQty)/maxQty)*100}%;"></div>
        <input type="range" min="0" max="${maxQty}" value="${qtyMin||0}" class="dual-slider-input" style="z-index:2;" oninput="updateDualSlider('qty', 'min', this.value, ${maxQty})">
        <input type="range" min="0" max="${maxQty}" value="${qtyMax||maxQty}" class="dual-slider-input" style="z-index:3;" oninput="updateDualSlider('qty', 'max', this.value, ${maxQty})">
      </div>
    </div>
    <div class="filter-section"><p style="font-size:12px;font-weight:600;color:#374151;margin-bottom:4px;">Categories (${selectedCats.length} selected)</p>${visibleCats.map(c => `<label style="display:flex;align-items:center;gap:6px;margin:4px 0;cursor:pointer;"><input type="checkbox" ${selectedCats.includes(c)?'checked':''} onchange="toggleCat('${c}')" style="cursor:pointer;" /> <span style="${selectedCats.includes(c)?'font-weight:600;color:#5c2145;':''}">${c}</span></label>`).join('')}${cats.length > MAX_VISIBLE ? `<button onclick="toggleShowAllCats()" style="margin-top:8px;padding:6px 12px;background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;cursor:pointer;font-size:11px;color:#5c2145;width:100%;text-align:center;transition:all 0.2s;" onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='#f8f9fa'">${showAllCats ? 'Show Less ↑' : `Show All (${cats.length}) ↓`}</button>` : ''}</div>
    <div class="filter-section"><p style="font-size:12px;font-weight:600;color:#374151;margin-bottom:4px;">Brands (${selectedBrands.length} selected)</p>${visibleBrands.map(b => `<label style="display:flex;align-items:center;gap:6px;margin:4px 0;cursor:pointer;"><input type="checkbox" ${selectedBrands.includes(b)?'checked':''} onchange="toggleBrand('${b}')" style="cursor:pointer;" /> <span style="${selectedBrands.includes(b)?'font-weight:600;color:#5c2145;':''}">${b}</span></label>`).join('')}${brands.length > MAX_VISIBLE ? `<button onclick="toggleShowAllBrands()" style="margin-top:8px;padding:6px 12px;background:#f8f9fa;border:1px solid #dee2e6;border-radius:6px;cursor:pointer;font-size:11px;color:#5c2145;width:100%;text-align:center;transition:all 0.2s;" onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='#f8f9fa'">${showAllBrands ? 'Show Less ↑' : `Show All (${brands.length}) ↓`}</button>` : ''}</div>
    <div class="filter-actions">
      <button class="btn btn-primary btn-sm" style="flex:1" onclick="render()">Apply Filters</button>
      <button class="btn btn-outline btn-sm" style="flex:1" onclick="clearFilters()">Clear</button>
    </div>`;
}

function toggleCat(c) { selectedCats.includes(c) ? selectedCats = selectedCats.filter(x=>x!==c) : selectedCats.push(c); render(); }
function toggleBrand(b) { selectedBrands.includes(b) ? selectedBrands = selectedBrands.filter(x=>x!==b) : selectedBrands.push(b); render(); }
function toggleShowAllCats() { showAllCats = !showAllCats; renderFilters(); }
function toggleShowAllBrands() { showAllBrands = !showAllBrands; renderFilters(); }
let renderTimeout = null;

function debouncedRender() {
  if (renderTimeout) clearTimeout(renderTimeout);
  renderTimeout = setTimeout(() => render(), 50);
}

function updateDualSlider(type, thumb, value, maxVal) {
  const val = parseInt(value) || 0;
  if (type === 'price') {
    if (thumb === 'min') {
      priceMin = Math.min(val, parseInt(priceMax || maxVal) - 1);
    } else {
      priceMax = Math.max(val, parseInt(priceMin || 0) + 1);
    }
    const minPct = (parseInt(priceMin || 0) / maxVal) * 100;
    const widthPct = ((parseInt(priceMax || maxVal) - parseInt(priceMin || 0)) / maxVal) * 100;
    const fill = document.getElementById('priceFill');
    const thumbMin = document.getElementById('priceThumbMin');
    const thumbMax = document.getElementById('priceThumbMax');
    if (fill) {
      fill.style.left = minPct + '%';
      fill.style.width = widthPct + '%';
    }
    if (thumbMin) thumbMin.style.left = minPct + '%';
    if (thumbMax) thumbMax.style.left = ((parseInt(priceMax || maxVal) / maxVal) * 100) + '%';
    const minInput = document.getElementById('priceMinInput');
    const maxInput = document.getElementById('priceMaxInput');
    if (minInput) minInput.value = priceMin;
    if (maxInput) maxInput.value = priceMax;
  } else {
    if (thumb === 'min') {
      qtyMin = Math.min(val, parseInt(qtyMax || maxVal) - 1);
    } else {
      qtyMax = Math.max(val, parseInt(qtyMin || 0) + 1);
    }
    const minPct = (parseInt(qtyMin || 0) / maxVal) * 100;
    const widthPct = ((parseInt(qtyMax || maxVal) - parseInt(qtyMin || 0)) / maxVal) * 100;
    const fill = document.getElementById('qtyFill');
    const thumbMin = document.getElementById('qtyThumbMin');
    const thumbMax = document.getElementById('qtyThumbMax');
    if (fill) {
      fill.style.left = minPct + '%';
      fill.style.width = widthPct + '%';
    }
    if (thumbMin) thumbMin.style.left = minPct + '%';
    if (thumbMax) thumbMax.style.left = ((parseInt(qtyMax || maxVal) / maxVal) * 100) + '%';
    const minInput = document.getElementById('qtyMinInput');
    const maxInput = document.getElementById('qtyMaxInput');
    if (minInput) minInput.value = qtyMin;
    if (maxInput) maxInput.value = qtyMax;
  }
  debouncedRender();
}

function updatePriceFilter(thumb, value) {
  const val = parseInt(value) || 0;
  const allProducts = products;
  const maxPrice = allProducts.length > 0 ? Math.max(...allProducts.map(p => p.price)) : 100000;
  
  if (thumb === 'min') {
    priceMin = Math.min(val, parseInt(priceMax || maxPrice) - 1);
  } else {
    priceMax = Math.max(val, parseInt(priceMin || 0) + 1);
  }
  
  const minPct = (parseInt(priceMin || 0) / maxPrice) * 100;
  const widthPct = ((parseInt(priceMax || maxPrice) - parseInt(priceMin || 0)) / maxPrice) * 100;
  const fill = document.getElementById('priceFill');
  const thumbMin = document.getElementById('priceThumbMin');
  const thumbMax = document.getElementById('priceThumbMax');
  if (fill) {
    fill.style.left = minPct + '%';
    fill.style.width = widthPct + '%';
  }
  if (thumbMin) thumbMin.style.left = minPct + '%';
  if (thumbMax) thumbMax.style.left = ((parseInt(priceMax || maxPrice) / maxPrice) * 100) + '%';
  
  debouncedRender();
}

function updateQtyFilter(thumb, value) {
  const val = parseInt(value) || 0;
  const allProducts = products;
  const maxQty = allProducts.length > 0 ? Math.max(...allProducts.map(p => p.quantity)) : 1000;
  
  if (thumb === 'min') {
    qtyMin = Math.min(val, parseInt(qtyMax || maxQty) - 1);
  } else {
    qtyMax = Math.max(val, parseInt(qtyMin || 0) + 1);
  }
  
  const minPct = (parseInt(qtyMin || 0) / maxQty) * 100;
  const widthPct = ((parseInt(qtyMax || maxQty) - parseInt(qtyMin || 0)) / maxQty) * 100;
  const fill = document.getElementById('qtyFill');
  const thumbMin = document.getElementById('qtyThumbMin');
  const thumbMax = document.getElementById('qtyThumbMax');
  if (fill) {
    fill.style.left = minPct + '%';
    fill.style.width = widthPct + '%';
  }
  if (thumbMin) thumbMin.style.left = minPct + '%';
  if (thumbMax) thumbMax.style.left = ((parseInt(qtyMax || maxQty) / maxQty) * 100) + '%';
  
  debouncedRender();
}
function clearFilters() { selectedCats=[]; selectedBrands=[]; showAllCats=false; showAllBrands=false; priceMin=''; priceMax=''; qtyMin=''; qtyMax=''; document.getElementById('searchInput').value=''; currentPage=1; render(); }
function changePageSize(size) { pageSize = parseInt(size); currentPage = 1; render(); }
function toggleAllCheckboxes(el) { document.querySelectorAll('.row-cb').forEach(cb => cb.checked = el.checked); }

function removeProduct(id) {
  fetch(`/products/${id}/`, {method: 'DELETE'})
  .then(response => {
    if (response.ok) {
      products = products.filter(p => p.id != id);
      render();
    }
  });
}

function addProduct(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById('addName').value.trim(),
    brand: document.getElementById('addBrand').value.trim(),
    category: document.getElementById('addCategory').value.trim(),
    description: document.getElementById('addDesc').value.trim(),
    price: parseFloat(document.getElementById('addPrice').value) || 0,
    quantity: parseInt(document.getElementById('addQty').value) || 0,
    policy: {
      warranty_period: document.getElementById('addWarranty').value.trim(),
      return_window: document.getElementById('addReturn').value.trim(),
      refund_policy: document.getElementById('addRefund').value.trim(),
      vendor_faq_link: document.getElementById('addFAQ').value.trim()
    }
  };
  fetch('/products/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Failed to add product');
    }
  })
  .then(newProduct => {
    products.push({
      id: newProduct.id,
      name: newProduct.name,
      brand: newProduct.brand,
      category: newProduct.category,
      description: newProduct.description,
      price: newProduct.price,
      quantity: newProduct.quantity,
      policy: newProduct.policy || {
        warranty_period: '',
        return_window: '',
        refund_policy: '',
        vendor_faq_link: ''
      }
    });
    e.target.reset();
    render();
  })
  .catch(e => {
    console.error('Error adding product', e);
  });
}

function parseCSVLine(line) {
  // Proper CSV parser that handles quoted fields containing commas.
  const result = [];
  let cur = '', inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i+1] === '"') { cur += '"'; i++; } // escaped quote ""
      else inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      result.push(cur.trim()); cur = '';
    } else {
      cur += ch;
    }
  }
  result.push(cur.trim());
  return result;
}

function bulkUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    const lines = ev.target.result.split('\n').filter(l => l.trim());
    if (lines.length < 2) return;
    const headers = parseCSVLine(lines[0]).map(h => h.toLowerCase().replace(/\s+/g, '_'));
    const idx = k => headers.indexOf(k);
    const items = [];
    lines.slice(1).forEach(l => {
      const cols = parseCSVLine(l);
      const name        = cols[idx('name')]        || '';
      const brand       = cols[idx('brand')]       || '';
      const category    = cols[idx('category')]    || '';
      const description = cols[idx('description')] || '';
      const price       = cols[idx('price')]       || '0';
      const quantity    = cols[idx('quantity')]    || '0';
      const warranty    = cols[idx('warranty_period')]   || '';
      const return_win  = cols[idx('return_window')]     || '';
      const refund      = cols[idx('refund_policy')]   || '';
      const faq_link    = cols[idx('vendor_faq_link')] || '';
      if (name && brand && category) {
        items.push({
          name: name.trim(),
          brand: brand.trim(),
          category: category.trim(),
          description: description.trim(),
          price: parseFloat(price) || 0,
          quantity: parseInt(quantity) || 0,
          policy: {
            warranty_period: warranty.trim(),
            return_window: return_win.trim(),
            refund_policy: refund.trim(),
            vendor_faq_link: faq_link.trim()
          }
        });
      }
    });
    if (items.length > 0) {
      fetch('/products/bulk/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(items)
      })
      .then(response => {
        if (response.ok) {
          loadProducts();
        } else {
          console.error('Bulk upload failed');
        }
      });
    }
  };
  reader.readAsText(file);
  e.target.value = '';
}

function exportCSV() {
  const filtered = getFiltered();
  const selectedCheckboxes = document.querySelectorAll('.row-cb:checked');
  
  if (selectedCheckboxes.length === 0) {
    alert('Please select at least one product to export.');
    return;
  }
  
  // Get only selected products
  const selectedProducts = [];
  selectedCheckboxes.forEach(checkbox => {
    const row = checkbox.closest('tr');
    if (row) {
      const productName = row.querySelector('.prod-name')?.textContent || '';
      const product = filtered.find(p => p.name === productName);
      if (product) {
        selectedProducts.push(product);
      }
    }
  });
  
  // Description must be at index 3 to match bulkUpload's positional destructuring.
  // Quote fields so commas inside descriptions don't break CSV parsing.
  const esc = s => '"' + String(s||'').replace(/"/g, '""') + '"';
  const rows = [['Name','Brand','Category','Description','Price','Quantity','Warranty_Period','Return_Window','Refund_Policy','Vendor_FAQ_Link']];
  selectedProducts.forEach(p => rows.push([esc(p.name),esc(p.brand),esc(p.category),esc(p.description),p.price,p.quantity,esc(p.policy?.warranty_period),esc(p.policy?.return_window),esc(p.policy?.refund_policy),esc(p.policy?.vendor_faq_link)]));
  const csv = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'selected_inventory.csv';
  a.click();
}

function renderCharts(filtered) {
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const ctx = document.getElementById('mainChart');
  if (!ctx) return;
  
  switch(currentChart) {
    case 'stock':
      renderStockChart(filtered, ctx);
      break;
    case 'category':
      renderCategoryChart(filtered, ctx);
      break;
    case 'brand':
      renderBrandChart(filtered, ctx);
      break;
    case 'price':
      renderPriceChart(filtered, ctx);
      break;
    case 'value':
      renderValueChart(filtered, ctx);
      break;
  }
}

function switchChart(type) {
  currentChart = type;
  document.querySelectorAll('.chart-btn').forEach(btn => { btn.style.background='#f8f9fa'; btn.style.color='#5c2145'; });
  const activeBtn = document.getElementById('btn-'+type);
  if (activeBtn) { activeBtn.style.background='#5c2145'; activeBtn.style.color='white'; }
  const panel = document.getElementById('pieLegendScroll');
  if (panel) panel.style.display = (type==='category'||type==='brand') ? 'block' : 'none';
  const outer = document.getElementById('chartOuter');
  if (outer) outer.style.height = '300px';
  renderCharts(getFiltered());
}

function renderStockChart(filtered, ctx) {
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: filtered.map(p => p.name.length > 14 ? p.name.slice(0,14)+'…' : p.name),
      datasets: [{
        label: 'Quantity',
        data: filtered.map(p => p.quantity),
        backgroundColor: filtered.map(p => p.quantity <= LOW_STOCK ? 'rgba(220,53,69,0.75)' : 'rgba(92,33,69,0.75)'),
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, title: { display: true, text: 'Stock Levels', font: { size: 14 } } },
      scales: {
        x: { ticks: { font: { size: 10 }, maxRotation: 45 }, grid: { display: false } },
        y: { ticks: { font: { size: 11 } }, grid: { color: 'rgba(0,0,0,.06)' } }
      }
    }
  });
}

function genDistinctColors(n) {
  const bands = [{s:70,l:42},{s:55,l:60},{s:80,l:35},{s:45,l:68},{s:90,l:50},{s:40,l:52},{s:65,l:30},{s:60,l:72}];
  return Array.from({length:n},(_,i)=>`hsl(${Math.round(i*360/n)},${bands[i%bands.length].s}%,${bands[i%bands.length].l}%)`);
}

function renderCategoryChart(filtered, ctx) {
  const cats = [...new Set(filtered.map(p => p.category))].sort();
  const counts = cats.map(c => filtered.filter(p => p.category === c).length);
  const total = counts.reduce((a,b)=>a+b,0);
  const colors = genDistinctColors(cats.length);
  const panel = document.getElementById('pieLegendScroll');
  if (panel) {
    panel.innerHTML = '<div style="font-size:11px;font-weight:700;color:#5c2145;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #f0e8ed;">Categories</div>'
      + cats.map((cat,i)=>{
          const pct = total>0?((counts[i]/total)*100).toFixed(1):'0.0';
          const lbl = cat.length>18?cat.slice(0,17)+'…':cat;
          return `<div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:10.5px;color:#333;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${colors[i]};flex-shrink:0;"></span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${cat}">${lbl}</span><span style="color:#5c2145;font-weight:600;flex-shrink:0;">${pct}%</span></div>`;
        }).join('');
  }
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: { labels: cats, datasets: [{ data: counts, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }] },
    options: {
      responsive: true, maintainAspectRatio: false, layout: { padding: 8 },
      plugins: {
        title: { display: true, text: 'Category Distribution', font: { size: 14 } },
        legend: { display: false },
        tooltip: { callbacks: { label: c => ` ${c.label}: ${c.parsed} (${total>0?((c.parsed/total)*100).toFixed(1):0}%)` } }
      },
      cutout: '58%'
    }
  });
}

function renderBrandChart(filtered, ctx) {
  const brands = [...new Set(filtered.map(p => p.brand))].sort();
  const counts = brands.map(b => filtered.filter(p => p.brand === b).length);
  const total = counts.reduce((a,b)=>a+b,0);
  const colors = genDistinctColors(brands.length);
  const panel = document.getElementById('pieLegendScroll');
  if (panel) {
    panel.innerHTML = '<div style="font-size:11px;font-weight:700;color:#2d5a4a;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #e8f0ed;">Brands</div>'
      + brands.map((brand,i)=>{
          const pct = total>0?((counts[i]/total)*100).toFixed(1):'0.0';
          const lbl = brand.length>18?brand.slice(0,17)+'…':brand;
          return `<div style="display:flex;align-items:center;gap:6px;padding:3px 0;font-size:10.5px;color:#333;"><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${colors[i]};flex-shrink:0;"></span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${brand}">${lbl}</span><span style="color:#2d5a4a;font-weight:600;flex-shrink:0;">${pct}%</span></div>`;
        }).join('');
  }
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: { labels: brands, datasets: [{ data: counts, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }] },
    options: {
      responsive: true, maintainAspectRatio: false, layout: { padding: 8 },
      plugins: {
        title: { display: true, text: 'Brand Distribution', font: { size: 14 } },
        legend: { display: false },
        tooltip: { callbacks: { label: c => ` ${c.label}: ${c.parsed} (${total>0?((c.parsed/total)*100).toFixed(1):0}%)` } }
      },
      cutout: '58%'
    }
  });
}

function renderPriceChart(filtered, ctx) {
  const ranges = ['< ₹500', '₹500-1000', '₹1000-2000', '₹2000-5000', '> ₹5000'];
  const counts = [
    filtered.filter(p => p.price < 500).length,
    filtered.filter(p => p.price >= 500 && p.price < 1000).length,
    filtered.filter(p => p.price >= 1000 && p.price < 2000).length,
    filtered.filter(p => p.price >= 2000 && p.price < 5000).length,
    filtered.filter(p => p.price >= 5000).length
  ];
  
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ranges,
      datasets: [{
        label: 'Products',
        data: counts,
        backgroundColor: 'rgba(92,33,69,0.7)',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { display: false },
        title: { display: true, text: 'Price Range Distribution', font: { size: 14 } }
      },
      scales: {
        x: { ticks: { font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { font: { size: 11 } }, grid: { color: 'rgba(0,0,0,.06)' } }
      }
    }
  });
}

function renderValueChart(filtered, ctx) {
  const cats = [...new Set(filtered.map(p => p.category))].sort();
  const values = cats.map(c =>
    filtered.filter(p => p.category === c).reduce((sum, p) => sum + (p.price * p.quantity), 0)
  );
  const paired = cats.map((c,i)=>({cat:c,val:values[i]})).sort((a,b)=>b.val-a.val);
  const sortedCats   = paired.map(x=>x.cat);
  const sortedValues = paired.map(x=>x.val);

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sortedCats.map(c => c.length>13 ? c.slice(0,12)+'…' : c),
      datasets: [{
        label: 'Value (₹)',
        data: sortedValues,
        backgroundColor: 'rgba(45,90,74,0.75)',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Inventory Value by Category (₹)', font: { size: 14 } },
        tooltip: {
          callbacks: {
            title: items => sortedCats[items[0].dataIndex],
            label: c => ' ₹' + Number(c.parsed.y).toLocaleString('en-IN')
          }
        }
      },
      scales: {
        x: { ticks: { font: { size: 9 }, maxRotation: 40, autoSkip: false }, grid: { display: false } },
        y: {
          title: { display: true, text: 'Value (₹)', font: { size: 11 } },
          ticks: {
            font: { size: 10 },
            callback: v => {
              if (v===0) return '₹0';
              if (v>=100000) return '₹'+(v/100000).toFixed(1)+'L';
              if (v>=1000)   return '₹'+(v/1000).toFixed(0)+'k';
              return '₹'+v;
            }
          },
          grid: { color: 'rgba(0,0,0,.06)' }
        }
      }
    }
  });
}

loadProducts();

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function addAiMessage(text, isUser) {
  const container = document.getElementById('aiChatMessages');
  if (!container) return;

  const row = document.createElement('div');
  row.className = 'msg-row ' + (isUser ? 'user' : 'bot');

  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formatted = isUser ? text.replace(/\n/g, '<br>') : formatMarkdown(text);

  if (isUser) {
    row.innerHTML = `<div class="bubble">${formatted}<span class="timestamp">${time}</span></div>`;
  } else {
    row.innerHTML = `<div class="bot-avatar" style="display:flex;align-items:center;justify-content:center;"><img src="${window.ICON_URL}" alt="Rippling" style="width:22px;height:22px;object-fit:contain;border-radius:5px;"></div><div class="bubble" style="line-height: 1.6;">${formatted}<span class="timestamp">${time}</span></div>`;
  }

  container.appendChild(row);
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

let pendingAiProducts = [];
let aiLoadingInterval = null;
let aiLoadingMsgIndex = null;
const aiLoadingMessages = [
  'Thinking...',
  'Generating inventory...',
  'Building products...',
  'Almost done...',
  'Finalizing details...'
];

// AI Inventory Chat History State
let aiChats = [];
let currentAiChatId = null;
let aiCurrentChatTitle = 'New Chat';
let aiChatHistory = [];
let isAiChatSidebarOpen = true;

function getAiChatById(id) {
  return aiChats.find(c => c.id === id);
}

function setAiChatTitle(title) {
  aiCurrentChatTitle = title || 'New Chat';
  const titleEl = document.getElementById('aiChatTitle');
  if (titleEl) titleEl.textContent = aiCurrentChatTitle;
  
  // Update the chat object in the array
  const currentChat = getAiChatById(currentAiChatId);
  if (currentChat) {
    currentChat.title = aiCurrentChatTitle;
    currentChat.updated_at = new Date().toISOString();
    saveAiChatsToLocal();
    renderAiChatList(); // Re-render the chat list to show the updated title
  }
}

function renderAiChatMessages() {
  const container = document.getElementById('aiChatMessages');
  if (!container) return;
  container.innerHTML = '';

  if (!aiChatHistory || aiChatHistory.length === 0) {
    addAiMessage('Hi! Describe what products you need. Example: "Create 15 outdoor summer toys"', false);
    return;
  }

  (aiChatHistory || []).forEach(msg => {
    addAiMessage(msg.content, msg.role === 'user');
  });
}

function renderAiChatList() {
  const list = document.getElementById('aiChatList');
  if (!list) return;
  if (!aiChats || aiChats.length === 0) {
    list.innerHTML = '<div style="padding: 12px; text-align: center; color: #64748b; font-size: 12px;">No chats yet</div>';
    return;
  }

  list.innerHTML = aiChats.map(chat => {
    const preview = chat.messages && chat.messages.length > 0 ? chat.messages[0].content.substring(0, 30) + '...' : 'No messages yet';
    const date = new Date(chat.updated_at || chat.updatedAt || Date.now());
    const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const isActive = chat.id === currentAiChatId;
    return `
      <div class="history-item ${isActive ? 'active' : ''}" style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; cursor: pointer; transition: background .15s;" onclick="if(event.target.closest('.delete-btn')) return; loadAiChat('${chat.id}')">
        <div style="flex: 1; min-width: 0; overflow: hidden;">
          <div class="title">${chat.title}</div>
          <div class="preview">${preview}</div>
          <div class="time">${dateStr}</div>
        </div>
        <button class="delete-btn" onclick="deleteAiChat('${chat.id}')" 
                style="width: 24px; height: 24px; border: none; background: transparent; color: ${isActive ? 'rgba(255,255,255,0.7)' : '#94a3b8'}; 
                       cursor: pointer; border-radius: 6px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; margin-left: 8px;"
                onmouseover="this.style.background='${isActive ? 'rgba(255,255,255,0.2)' : '#fee2e2'}'; this.style.color='${isActive ? '#fff' : '#dc2626'}';"
                onmouseout="this.style.background='transparent'; this.style.color='${isActive ? 'rgba(255,255,255,0.7)' : '#94a3b8'}';"
                title="Delete chat">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    `;
  }).join('');
}

function loadAiChat(chatId) {
  currentAiChatId = chatId;
  const chat = getAiChatById(chatId);
  if (!chat) return;
  setAiChatTitle(chat.title || 'New Chat');
  aiChatHistory = chat.messages || [];
  renderAiChatMessages();
  renderAiChatList();
}

async function deleteAiChat(chatId) {
  if (!chatId) return;
  const chat = getAiChatById(chatId);
  if (!chat) return;

  try {
    const csrfToken = getCookie('csrftoken');
    await fetch('/ai/chats/' + chatId + '/', {
      method: 'DELETE',
      headers: { 'X-CSRFToken': csrfToken }
    });
  } catch (e) {
    console.error('Failed to delete AI chat from backend:', e);
  }
  aiChats = aiChats.filter(c => c.id !== chatId);
  saveAiChatsToLocal();
  showToast(`\"${chat.title || 'Chat'}\" deleted`, 'success');

  if (currentAiChatId === chatId) {
    if (aiChats.length > 0) {
      loadAiChat(aiChats[0].id);
    } else {
      createNewAiChat();
    }
  } else {
    renderAiChatList();
  }
}

function toggleAiChatSidebar() {
  isAiChatSidebarOpen = !isAiChatSidebarOpen;
  const sidebar = document.getElementById('aiChatSidebar');
  if (sidebar) {
    sidebar.classList.toggle('expanded', isAiChatSidebarOpen);
  }

  const toggleIcon = document.getElementById('aiSidebarToggleIcon');
  const toggleBtn = document.getElementById('aiChatSidebarToggle');
  if (toggleIcon) {
    toggleIcon.innerHTML = isAiChatSidebarOpen
      ? '<polyline points="15 18 9 12 15 6"/>'
      : '<polyline points="9 18 15 12 9 6"/>';
  }
  if (toggleBtn) {
    toggleBtn.title = isAiChatSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar';
  }
}

async function createNewAiChat() {
  const newChat = {
    id: Date.now().toString(),
    title: 'New Chat',
    messages: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };

  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/ai/chats/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ title: newChat.title })
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.chat) {
        newChat.id = data.chat.id;
      }
    }
  } catch (e) {
    console.error('Failed to create AI chat in backend:', e);
  }

  aiChats.unshift(newChat);
  saveAiChatsToLocal();
  currentAiChatId = newChat.id;
  setAiChatTitle(newChat.title);
  aiChatHistory = [];
  renderAiChatMessages();
  renderAiChatList();
}

function saveAiChatsToLocal() {
  localStorage.setItem('aiChats', JSON.stringify(aiChats));
}

async function syncAiChatToMongo() {
  if (!currentAiChatId) return;
  const chat = getAiChatById(currentAiChatId);
  if (!chat) return;

  try {
    const csrfToken = getCookie('csrftoken');
    const cleanMessages = (chat.messages || []).filter(m => !m._loading);
    const response = await fetch('/ai/chats/sync/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        chat_id: chat.id,
        messages: cleanMessages,
        title: chat.title
      })
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        saveAiChatsToLocal();
      }
    }
  } catch (e) {
    console.error('Failed to sync AI chat to backend:', e);
  }
}

function loadAiChats() {
  // Load from backend if available, otherwise fallback to localStorage
  fetch('/ai/chats/', { headers: { 'X-CSRFToken': getCookie('csrftoken') } })
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (data && data.chats && data.chats.length > 0) {
        aiChats = data.chats;
        saveAiChatsToLocal();
        renderAiChatList();
        if (!currentAiChatId) {
          loadAiChat(aiChats[0].id);
        }
      } else {
        const stored = localStorage.getItem('aiChats');
        if (stored) {
          aiChats = JSON.parse(stored);
          renderAiChatList();
          if (!currentAiChatId && aiChats.length > 0) {
            loadAiChat(aiChats[0].id);
          }
        } else {
          createNewAiChat();
        }
      }
    }).catch(() => {
      const stored = localStorage.getItem('aiChats');
      if (stored) {
        aiChats = JSON.parse(stored);
        renderAiChatList();
        if (!currentAiChatId && aiChats.length > 0) {
          loadAiChat(aiChats[0].id);
        }
      } else {
        createNewAiChat();
      }
    });
}

function generateAiChatTitle(firstMessage) {
  return fetch('/rag/generate-title/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ message: firstMessage })
  })
  .then(r => r.ok ? r.json() : null)
  .then(data => (data && data.success && data.title) ? data.title : null)
  .catch(() => null);
}

function showPolicyTooltip(event) {
  const btn = event.currentTarget;
  const raw = btn.dataset.policy || '';
  const policyText = decodeURIComponent(raw);
  if (!policyText) return;
  let tooltip = document.getElementById('policyTooltipBubble');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'policyTooltipBubble';
    tooltip.style.cssText = 'position: fixed; background: white; color: #0f172a; padding: 12px 16px; border-radius: 12px; font-size: 12px; white-space: pre-line; z-index: 999999; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border: 1px solid rgba(92,33,69,0.15); max-width: 300px; line-height: 1.5;';
    document.body.appendChild(tooltip);
  }
  
  // Format the policy text without emojis, proper bold rendering
  const formattedText = policyText
    .replace(/Warranty:/gi, '<strong>Warranty:</strong>')
    .replace(/Return:/gi, '<strong>Return:</strong>')
    .replace(/Refund:/gi, '<strong>Refund:</strong>')
    .replace(/N\/A/gi, 'Not specified');
  
  tooltip.innerHTML = formattedText;
  tooltip.style.display = 'block';
  const rect = btn.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  const left = Math.min(Math.max(rect.left + rect.width / 2 - tooltipRect.width / 2, 8), window.innerWidth - tooltipRect.width - 8);
  const top = rect.top - tooltipRect.height - 8;
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top > 8 ? top : rect.bottom + 8}px`;
}

function hidePolicyTooltip() {
  const tooltip = document.getElementById('policyTooltipBubble');
  if (tooltip) tooltip.style.display = 'none';
}

function showAiLoadingMessage() {
  if (aiLoadingMsgIndex !== null) return;

  // Add a placeholder assistant message at the end (with spinner + animated dots)
  aiLoadingMsgIndex = aiChatHistory.length;
  const initialText = `<span class="loading-dots">${aiLoadingMessages[0]}</span>`;
  aiChatHistory.push({ role: 'assistant', content: initialText, _loading: true });
  renderAiChatMessages();

  let msgIndex = 0;
  aiLoadingInterval = setInterval(() => {
    msgIndex = (msgIndex + 1) % aiLoadingMessages.length;
    if (aiLoadingMsgIndex !== null && aiChatHistory[aiLoadingMsgIndex]) {
      aiChatHistory[aiLoadingMsgIndex].content = `<span class="loading-dots">${aiLoadingMessages[msgIndex]}</span>`;
      renderAiChatMessages();
    }
  }, 2000);
}

function hideAiLoadingMessage(replacementText) {
  if (aiLoadingInterval) {
    clearInterval(aiLoadingInterval);
    aiLoadingInterval = null;
  }
  if (aiLoadingMsgIndex !== null) {
    if (typeof replacementText === 'string') {
      aiChatHistory[aiLoadingMsgIndex].content = replacementText;
      delete aiChatHistory[aiLoadingMsgIndex]._loading;
    } else {
      aiChatHistory.splice(aiLoadingMsgIndex, 1);
    }
    aiLoadingMsgIndex = null;
    renderAiChatMessages();
  }
}

async function sendAiMessage() {
  const input = document.getElementById('scenarioInput');
  const countInput = document.getElementById('aiProductCount');
  const btn = document.getElementById('aiSendBtn');
  const sendIcon = document.getElementById('aiSendIcon');
  const loadingIcon = document.getElementById('aiLoadingIcon');
  const text = input.value.trim();
  const count = countInput ? (parseInt(countInput.value) || 10) : 10;

  if (!text) {
    addAiMessage('Please enter a message!', false);
    return;
  }

  // Add the user message to the local chat history and render it immediately.
  addAiMessage(text, true);
  btn.disabled = true;
  sendIcon.style.display = 'none';
  loadingIcon.style.display = 'inline';
  input.value = '';
  const aiPreviewSection = document.getElementById('aiPreviewSection');
  if (aiPreviewSection) aiPreviewSection.style.display = 'none';

  try {
    // Ensure there is an active chat session to store history
    if (!currentAiChatId) {
      await createNewAiChat();
    }
    if (!Array.isArray(aiChatHistory)) aiChatHistory = [];
    aiChatHistory.push({ role: 'user', content: text });
    renderAiChatMessages();

    // Show a "thinking" indicator message after the user message
    showAiLoadingMessage();

    // Update local chat state and optionally generate a title if it's still the default
    const currentChat = getAiChatById(currentAiChatId);
    if (currentChat) {
      currentChat.messages = aiChatHistory;
      currentChat.updated_at = new Date().toISOString();
      if (!currentChat.title || currentChat.title === 'New Chat') {
        const generatedTitle = await generateAiChatTitle(text);
        if (generatedTitle) {
          currentChat.title = generatedTitle;
          setAiChatTitle(generatedTitle);
        }
      }
      saveAiChatsToLocal();
    }

    // Sync chat to MongoDB before sending
    await syncAiChatToMongo();

    console.log('Sending AI request:', { scenario_text: text, count: count, chat_history: aiChatHistory });

    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
      addAiMessage('Error: CSRF token not found. Please refresh the page.', false);
      return;
    }
    
    // Create AbortController for timeout
    const controller = new AbortController();
    let timeoutId = setTimeout(() => controller.abort(), 45000); // 45 second timeout for AI generation
    
    try {
      const response = await fetch('/ai/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ scenario_text: text, count: count, chat_history: aiChatHistory }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      console.log('Response status:', response.status);

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.error('Non-JSON response:', textResponse.substring(0, 200));
        addAiMessage('Server error: ' + response.status + ' - Please check console', false);
        return;
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      if (response.ok && data.success) {
        // Determine what to show in the chat bubble
        let responseText = '';
        if (data.intent === 'chat') {
          responseText = data.chat_message || 'I\'m here to help!';
        } else if (data.intent === 'product_generation') {
          if (data.products && data.products.length > 0) {
            responseText = data.chat_message || 'I have generated <strong>' + data.generated_count + '</strong> products for you! Please review them below.';
            pendingAiProducts = (data.products || []).map((p, idx) => ({
              ...p,
              _id: idx,
              _approved: null,
              policy: p.policy || {
                warranty_period: '',
                return_window: '',
                refund_policy: '',
                vendor_faq_link: ''
              }
            }));
            showAiPreview(data);
          } else {
            responseText = data.chat_message || 'I understood you want products, but could not generate any. Please try a more specific description.';
          }
        } else {
          // Fallback for backward compatibility
          if (data.products && data.products.length > 0) {
            responseText = 'I have generated <strong>' + data.generated_count + '</strong> products for you! Please review them below.';
            pendingAiProducts = (data.products || []).map((p, idx) => ({
              ...p,
              _id: idx,
              _approved: null,
              policy: p.policy || {
                warranty_period: '',
                return_window: '',
                refund_policy: '',
                vendor_faq_link: ''
              }
            }));
            showAiPreview(data);
          } else {
            responseText = data.chat_message || data.error || 'No products generated.';
          }
        }

        hideAiLoadingMessage(responseText);

        const currentChat = getAiChatById(currentAiChatId);
        if (currentChat) {
          currentChat.messages = aiChatHistory.filter(m => !m._loading);
          currentChat.updated_at = new Date().toISOString();
          saveAiChatsToLocal();
        }

        await syncAiChatToMongo();

      } else {
        // Handle different error statuses
        let errorText = 'Error: ';
        if (response.status === 429) {
          errorText = 'Too many requests. Please wait a moment and try again.';
        } else if (response.status >= 500) {
          errorText = 'Server error. The AI service is temporarily unavailable. Please try again later.';
        } else if (response.status === 401 || response.status === 403) {
          errorText = 'Authentication error. Please refresh the page and try again.';
        } else {
          errorText += (data.error || 'Unknown error');
        }
        hideAiLoadingMessage(errorText);
      }
    } catch (err) {
      // Clear timeout if it exists
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      let errorText = 'Failed: ';
      if (err.name === 'AbortError') {
        errorText = 'Request timed out. The AI service is taking too long to respond. Please try again with a simpler request.';
      } else if (err.message.includes('Failed to fetch')) {
        errorText = 'Network error. Please check your internet connection and try again.';
      } else if (err.message.includes('CSRF')) {
        errorText = 'Security error. Please refresh the page and try again.';
      } else {
        errorText += (err.message || err);
      }
      hideAiLoadingMessage(errorText);
      console.error('Fetch error:', err);
    } finally {
      btn.disabled = false;
      sendIcon.style.display = 'inline';
      loadingIcon.style.display = 'none';
      hideAiLoadingMessage();
    }
  } catch (err) {
    // Handle errors from the outer try block
    console.error('AI generation error:', err);
    hideAiLoadingMessage('An unexpected error occurred. Please try again.');
    btn.disabled = false;
    sendIcon.style.display = 'inline';
    loadingIcon.style.display = 'none';
  }
}

function updateThresholdDisplay(value) {
  document.getElementById('thresholdValue').textContent = value + '%';
}

function getSimilarityThreshold() {
  const slider = document.getElementById('similarityThreshold');
  return slider ? parseInt(slider.value) / 100 : 0.3;
}

function showAiPreview(data) {
  const previewSection = document.getElementById('aiPreviewSection');
  const statsDiv = document.getElementById('aiPreviewStats');
  const tableDiv = document.getElementById('aiPreviewTable');
  const doneBtn = document.getElementById('doneReviewingBtn');
  const rejectBtn = document.getElementById('rejectAllBtn');
  const approveBtn = document.getElementById('approveAllBtn');
  
  previewSection.style.display = 'block';
  
  // Enable/disable buttons based on product availability
  const hasProducts = pendingAiProducts && pendingAiProducts.length > 0;
  if (doneBtn) doneBtn.disabled = !hasProducts;
  if (rejectBtn) rejectBtn.disabled = !hasProducts;
  if (approveBtn) approveBtn.disabled = !hasProducts;
  
  const approvedCount = pendingAiProducts.filter(p => p._approved === true).length;
  const rejectedCount = pendingAiProducts.filter(p => p._approved === false).length;
  const pendingCount = pendingAiProducts.filter(p => p._approved === null).length;
  
  // Improved stats styling
  statsDiv.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; width: 100%;">
      <div style="text-align:center;padding:12px;background:linear-gradient(135deg, #f8f9fa, #e9ecef);border-radius:12px;border:1px solid #dee2e6;">
        <div style="font-size:24px;font-weight:700;color:#5c2145;margin-bottom:4px;">${pendingAiProducts.length}</div>
        <div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;">Total Products</div>
      </div>
      <div style="text-align:center;padding:12px;background:linear-gradient(135deg, #d4edda, #c3e6cb);border-radius:12px;border:1px solid #c3e6cb;">
        <div style="font-size:24px;font-weight:700;color:#28a745;margin-bottom:4px;">${approvedCount}</div>
        <div style="font-size:11px;color:#155724;text-transform:uppercase;letter-spacing:0.5px;">Approved</div>
      </div>
      <div style="text-align:center;padding:12px;background:linear-gradient(135deg, #f8d7da, #f5c6cb);border-radius:12px;border:1px solid #f5c6cb;">
        <div style="font-size:24px;font-weight:700;color:#dc3545;margin-bottom:4px;">${rejectedCount}</div>
        <div style="font-size:11px;color:#721c24;text-transform:uppercase;letter-spacing:0.5px;">Rejected</div>
      </div>
      <div style="text-align:center;padding:12px;background:linear-gradient(135deg, #fff3cd, #ffeaa7);border-radius:12px;border:1px solid #ffeaa7;">
        <div style="font-size:24px;font-weight:700;color:#856404;margin-bottom:4px;">${pendingCount}</div>
        <div style="font-size:11px;color:#856404;text-transform:uppercase;letter-spacing:0.5px;">Pending Review</div>
      </div>
    </div>
  `;
  
  // Improved table styling
  let tableHtml = `
    <div style="border:1px solid #e9ecef;border-radius:12px;overflow:hidden;background:white;">
      <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <thead style="background:linear-gradient(135deg, #5c2145, #8b3a5c);color:white;position:sticky;top:0;">
          <tr>
            <th style="padding:12px;text-align:left;font-weight:600;border-bottom:none;">Product Name</th>
            <th style="padding:12px;text-align:left;font-weight:600;border-bottom:none;">Brand</th>
            <th style="padding:12px;text-align:left;font-weight:600;border-bottom:none;">Category</th>
            <th style="padding:12px;text-align:right;font-weight:600;border-bottom:none;">Price</th>
            <th style="padding:12px;text-align:right;font-weight:600;border-bottom:none;">Quantity</th>
            <th style="padding:12px;text-align:center;font-weight:600;border-bottom:none;width:120px;">Action</th>
          </tr>
        </thead>
        <tbody>
  `;
  
  if (pendingAiProducts && pendingAiProducts.length > 0) {
    for (let i = 0; i < pendingAiProducts.length; i++) {
      const p = pendingAiProducts[i];
      const statusClass = p._approved === true ? 'style="background:#d4edda;"' : (p._approved === false ? 'style="background:#f8d7da;opacity:0.6;"' : '');
      const actionButtons = p._approved === null ? 
        `<div style="display:flex;gap:6px;justify-content:center;">
          <button onclick="approveProduct(${i})" style="padding:6px 12px;background:#28a745;color:white;border:none;border-radius:6px;cursor:pointer;font-size:11px;font-weight:600;transition:all 0.2s;" title="Accept" onmouseover="this.style.background='#218838'" onmouseout="this.style.background='#28a745'">✓ Accept</button>
          <button onclick="rejectProduct(${i})" style="padding:6px 12px;background:#dc3545;color:white;border:none;border-radius:6px;cursor:pointer;font-size:11px;font-weight:600;transition:all 0.2s;" title="Reject" onmouseover="this.style.background='#c82333'" onmouseout="this.style.background='#dc3545'">✕ Reject</button>
        </div>` :
        (p._approved === true ? '<span style="color:#28a745;font-weight:600;display:flex;align-items:center;justify-content:center;gap:4px;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg> Approved</span>' : '<span style="color:#dc3545;font-weight:600;display:flex;align-items:center;justify-content:center;gap:4px;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.708 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg> Rejected</span>');
      
      tableHtml += `
        <tr ${statusClass} style="border-bottom:1px solid #f1f3f5;transition:all 0.2s;">
          <td style="padding:12px;vertical-align:top;">
            <div style="font-weight:600;color:#0f172a;margin-bottom:2px;">${p.name}</div>
            ${p.description ? `<div style="font-size:11px;color:#64748b;line-height:1.3;">${p.description}</div>` : ''}
          </td>
          <td style="padding:12px;color:#64748b;">${p.brand}</td>
          <td style="padding:12px;">
            <span style="background:#e9ecef;color:#495057;padding:4px 8px;border-radius:6px;font-size:11px;font-weight:500;">${p.category}</span>
          </td>
          <td style="padding:12px;text-align:right;font-weight:600;color:#0f172a;">₹${p.price.toFixed(2)}</td>
          <td style="padding:12px;text-align:right;color:#64748b;">${p.quantity}</td>
          <td style="padding:12px;text-align:center;">${actionButtons}</td>
        </tr>
      `;
    }
  } else {
    tableHtml += '<tr><td colspan="6" style="padding:32px;text-align:center;color:#6c757d;font-style:italic;">No products to preview</td></tr>';
  }
  tableHtml += '</tbody></table></div>';
  tableDiv.innerHTML = tableHtml;
}

function approveProduct(index) {
  const p = pendingAiProducts[index];
  if (!p || p._saved) return;
  
  fetch('/products/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      name: p.name,
      brand: p.brand,
      category: p.category,
      description: p.description,
      price: p.price,
      quantity: p.quantity,
      policy: p.policy || {
        warranty_period: '',
        return_window: '',
        refund_policy: '',
        vendor_faq_link: ''
      }
    })
  }).then(r => {
    if (r.ok) {
      p._approved = true;
      p._saved = true;
      showAiPreview({});
      addAiMessage('✓ <strong>' + p.name + '</strong> added to inventory!', false);
      loadProducts();
    } else {
      addAiMessage('✗ Failed to add <strong>' + p.name + '</strong>', false);
    }
  });
}

function rejectProduct(index) {
  pendingAiProducts[index]._approved = false;
  showAiPreview({});
}

function saveApprovedProducts() {
  const toSave = pendingAiProducts.filter(p => p._approved === true && !p._saved);
  if (toSave.length === 0) return;
  let saved = 0;
  let promises = toSave.map(p => {
    return fetch('/products/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: p.name,
        brand: p.brand,
        category: p.category,
        description: p.description,
        price: p.price,
        quantity: p.quantity,
        policy: p.policy || {
          warranty_period: '',
          return_window: '',
          refund_policy: '',
          vendor_faq_link: ''
        }
      })
    }).then(r => { 
      if (r.ok) {
        saved++;
        p._saved = true;
      }
    });
  });
  Promise.all(promises).then(() => {
    if (saved > 0) {
      addAiMessage('<strong>' + saved + '</strong> product' + (saved > 1 ? 's' : '') + ' added to your inventory!', false);
      loadProducts();
    }
  });
}

function approveAiProducts() {
  const toApprove = pendingAiProducts.filter(p => p._approved === null);
  toApprove.forEach(p => p._approved = true);
  showAiPreview({});
  saveApprovedProducts();
}

function closeAiPreview() {
  const aiPreviewSection = document.getElementById('aiPreviewSection');
  if (aiPreviewSection) aiPreviewSection.style.display = 'none';
  const approvedCount = pendingAiProducts.filter(p => p._approved === true).length;
  const totalCount = pendingAiProducts.length;
  if (approvedCount > 0) {
    addAiMessage('Review complete! <strong>' + approvedCount + '</strong> of <strong>' + totalCount + '</strong> products were added to your inventory.', false);
  } else {
    addAiMessage('Review complete. No products were added to inventory.', false);
  }
  pendingAiProducts = [];
}

function rejectAiProducts() {
  pendingAiProducts = [];
  const aiPreviewSection = document.getElementById('aiPreviewSection');
  if (aiPreviewSection) aiPreviewSection.style.display = 'none';
  addAiMessage('All products rejected. You can generate new ones anytime.', false);
}

function showAiResults(data) {
  const section = document.getElementById('aiResultSection');
  const body = document.getElementById('aiResultBody');
  section.style.display = 'block';
  let html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px;padding:12px 16px;background:linear-gradient(135deg,#f8f9fa 0%,#fff 100%);border-radius:8px;border:1px solid #e9ecef;">';
  html += '<div style="text-align:center;padding:12px;background:var(--secondary);border-radius:6px;"><div style="font-size:24px;font-weight:700;color:var(--accent);">' + data.generated_count + '</div><div style="font-size:11px;color:var(--muted);">Generated</div></div>';
  html += '<div style="text-align:center;padding:12px;background:var(--secondary);border-radius:6px;"><div style="font-size:24px;font-weight:700;color:var(--success);">' + data.saved_count + '</div><div style="font-size:11px;color:var(--muted);">Saved</div></div>';
  html += '<div style="text-align:center;padding:12px;background:var(--secondary);border-radius:6px;"><div style="font-size:24px;font-weight:700;color:var(--danger);">' + data.invalid_count + '</div><div style="font-size:11px;color:var(--muted);">Invalid</div></div>';
  html += '<div style="text-align:center;padding:12px;background:var(--secondary);border-radius:6px;"><div style="font-size:24px;font-weight:700;color:var(--text);">' + data.requested_count + '</div><div style="font-size:11px;color:var(--muted);">Requested</div></div>';
  html += '</div>';
  if (data.products && data.products.length > 0) {
    html += '<p style="font-size:12px;color:var(--muted);margin-bottom:8px;">Preview of generated products:</p>';
    html += '<div class="table-wrap"><table class="table" style="font-size:12px;"><thead><tr><th>Name</th><th>Brand</th><th>Category</th><th style="text-align:right;">Price</th><th style="text-align:right;">Qty</th></tr></thead><tbody>';
    for (let i = 0; i < data.products.length; i++) {
      const p = data.products[i];
      html += '<tr><td><strong>' + p.name + '</strong></td><td>' + p.brand + '</td><td><span style="background:#e9ecef;padding:2px 6px;border-radius:4px;font-size:11px;">' + p.category + '</span></td><td style="text-align:right;">₹' + p.price.toFixed(2) + '</td><td style="text-align:right;">' + p.quantity + '</td></tr>';
    }
    html += '</tbody></table></div>';
  }
  body.innerHTML = html;
}

document.getElementById('scenarioInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendAiMessage(); }
});

function adjustCount(delta) {
  const input = document.getElementById('aiProductCount');
  let value = parseInt(input.value) || 10;
  value += delta;
}

function validateCount(input) {
  let value = parseInt(input.value) || 10;
  if (value < 1) value = 1;
  if (value > 50) value = 50;
  input.value = value;
}

function toggleSearchMode(mode) {
  const normalBtn = document.getElementById('normalSearchBtn');
  const semanticBtn = document.getElementById('semanticSearchBtn');
  const normalForm = document.getElementById('normalSearchForm');
  const semanticForm = document.getElementById('semanticSearchForm');
  
  if (mode === 'normal') {
    // Activate normal search
    normalBtn.style.background = '#5c2145';
    normalBtn.style.color = 'white';
    semanticBtn.style.background = 'white';
    semanticBtn.style.color = '#5c2145';
    
    // Expand normal form, collapse semantic form
    normalForm.style.width = '280px';
    normalForm.style.opacity = '1';
    semanticForm.style.width = '0';
    semanticForm.style.opacity = '0';
    
    // Clear semantic search when switching away
    setTimeout(() => {
      clearSemanticSearch();
    }, 400);
  } else {
    // Activate semantic search
    semanticBtn.style.background = '#5c2145';
    semanticBtn.style.color = 'white';
    normalBtn.style.background = 'white';
    normalBtn.style.color = '#5c2145';
    
    // Expand semantic form, collapse normal form
    semanticForm.style.width = '640px'; // Total width of semantic form content
    semanticForm.style.opacity = '1';
    normalForm.style.width = '0';
    normalForm.style.opacity = '0';
    
    // Clear normal search when switching away
    setTimeout(() => {
      document.getElementById('searchInput').value = '';
      render();
    }, 400);
  }
}

let currentSemanticResults = [];

async function performSemanticSearch() {
  const query = document.getElementById('semanticSearchInput').value.trim();
  if (!query) return;
  
  const btn = document.querySelector('#semanticSearchInput + button');
  btn.disabled = true;
  btn.textContent = 'Searching...';

  try {
    const csrfToken = getCookie('csrftoken');
    const categoryFilter = document.getElementById('semanticSearchCategory').value;
    const requestBody = { 
      query: query, 
      top_k: 10, 
      similarity_threshold: getSimilarityThreshold() 
    };
    if (categoryFilter) {
      requestBody.category_filter = categoryFilter;
    }
    
    const response = await fetch('/search/semantic/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(requestBody)
    });
    
    if (response.ok) {
      const data = await response.json();
      displaySemanticResults(data);
    } else {
      console.error('Semantic search failed:', response.status);
    }
  } catch (e) {
    console.error('Semantic search error:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Search';
  }
}

function displaySemanticResults(data) {
  const SIMILARITY_THRESHOLD = getSimilarityThreshold();
  
  const allResults = data.results || [];
  const filteredResults = allResults.filter(r => r.similarity_score >= SIMILARITY_THRESHOLD);
  const queryText = data.query;
  const totalResults = data.total_results || 0;
  
  document.getElementById('semanticSearchQuery').innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding:12px 16px;background:linear-gradient(135deg,#f8f9fa 0%,#fff 100%);border-radius:8px;border:1px solid #e9ecef;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;color:#5c2145;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <div style="flex:1;">
        <span style="color:#6c757d;font-size:12px;">Search query:</span>
        <span style="font-weight:600;color:#5c2145;margin-left:6px;">${queryText}</span>
        ${allResults.length > 0 ? `<span style="color:#adb5bd;font-size:11px;margin-left:12px;">Showing ${filteredResults.length} of ${allResults.length} above ${(SIMILARITY_THRESHOLD * 100).toFixed(0)}%</span>` : `<span style="color:#6c757d;font-size:12px;margin-left:12px;">${totalResults} result${totalResults !== 1 ? 's' : ''}</span>`}
      </div>
    </div>
  `;
  
  const resultsDiv = document.getElementById('semanticResultsList');
  if (filteredResults.length === 0) {
    resultsDiv.innerHTML = `
      <div style="text-align:center;padding:40px 20px;color:#6c757d;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;margin-bottom:12px;opacity:0.4;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <p style="font-size:14px;">No matching products found for this query.</p>
        ${allResults.length > 0 && filteredResults.length === 0 ? `<p style="font-size:12px;opacity:0.7;">Found ${allResults.length} products but none met the ${(SIMILARITY_THRESHOLD * 100).toFixed(0)}% similarity threshold.</p>` : `<p style="font-size:12px;opacity:0.7;">Try using different keywords or a more general description.</p>`}
      </div>
    `;
  } else {
    let html = '<div style="display:flex;flex-direction:column;gap:12px;">';
    for (let i = 0; i < filteredResults.length; i++) {
      const r = filteredResults[i];
      const p = r.product;
      const score = (r.similarity_score * 100).toFixed(1);
      const scoreColor = r.similarity_score > 0.7 ? '#28a745' : (r.similarity_score > 0.5 ? '#ffc107' : '#6c757d');
      const scoreLabel = r.similarity_score > 0.7 ? 'High Match' : (r.similarity_score > 0.5 ? 'Good Match' : 'Low Match');
      
      html += `
        <div style="display:flex;gap:16px;padding:16px;background:#fff;border:1px solid #e9ecef;border-radius:10px;transition:all 0.2s;box-shadow:0 1px 3px rgba(0,0,0,0.04);" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';this.style.transform='translateY(-2px)';this.style.borderColor='#5c2145';" onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.04)';this.style.transform='translateY(0)';this.style.borderColor='#e9ecef';">
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <span style="font-weight:600;font-size:14px;color:#212529;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.name}</span>
              <span style="background:#e9ecef;padding:2px 8px;border-radius:4px;font-size:11px;color:#5c2145;white-space:nowrap;">${p.category}</span>
            </div>
            <p style="color:#6c757d;font-size:12px;margin:0;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${p.description || 'No description available'}</p>
            <div style="display:flex;align-items:center;gap:16px;margin-top:8px;font-size:12px;">
              <span style="color:#5c2145;font-weight:500;">${p.brand}</span>
              <span style="color:#6c757d;">•</span>
              <span style="font-weight:600;">₹${p.price.toFixed(2)}</span>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:70px;padding-left:12px;border-left:1px solid #e9ecef;">
            <div style="font-size:22px;font-weight:700;color:${scoreColor};">${score}<span style="font-size:12px;">%</span></div>
            <div style="font-size:10px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;">${scoreLabel}</div>
          </div>
        </div>
      `;
    }
    html += '</div>';
    resultsDiv.innerHTML = html;
  }
  
  document.getElementById('semanticSearchResults').style.display = 'block';
  document.getElementById('semanticSearchResults').scrollIntoView({ behavior: 'smooth' });
}

function clearSemanticSearch() {
document.getElementById('semanticSearchResults').style.display = 'none';
document.getElementById('semanticSearchInput').value = '';
document.getElementById('semanticSearchCategory').value = '';
currentSemanticResults = [];
}

async function findSimilarProducts(productId) {
if (!productId) return;
  
try {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/search/similar/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({ product_id: productId, top_k: 5 })
  });
  
  if (response.ok) {
    const data = await response.json();
    showSimilarProductsModal(data);
  }
} catch (e) {
  console.error('Find similar error:', e);
}
}

function showSimilarProductsModal(data) {
  const SIMILARITY_THRESHOLD = 0.3;
  
  const modal = document.createElement('div');
  modal.id = 'similarProductsModal';
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:1000;display:flex;align-items:center;justify-content:center;animation:fadeIn 0.2s ease-out;';
  
  const productId = data.product_id || 'Selected Product';
  const allSimilarProducts = data.similar_products || [];
  const similarProducts = allSimilarProducts.filter(r => r.similarity_score >= SIMILARITY_THRESHOLD);
  
  let html = '<div style="background:#fff;border-radius:16px;padding:24px;max-width:700px;max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.4);animation:slideUp 0.3s ease-out;">';
  
  html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #e9ecef;">';
  html += '<div>';
  html += '<h3 style="margin:0 0 4px 0;display:flex;align-items:center;gap:10px;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:24px;height:24px;color:#5c2145;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="21.17" y1="4.83" x2="16.66" y2="9.34"/><line x1="7.34" y1="14.66" x2="2.83" y2="19.17"/></svg>Similar Products</h3>';
  html += '<span style="font-size:12px;opacity:0.9;">AI-powered recommendations based on semantic similarity</span>';
  if (allSimilarProducts.length > 0) {
    html += `<span style="display:block;margin-top:4px;font-size:11px;color:#adb5bd;">Showing results above ${(SIMILARITY_THRESHOLD * 100).toFixed(0)}% similarity (${similarProducts.length} of ${allSimilarProducts.length})</span>`;
  }
  html += '</div>';
  html += '<button onclick="document.getElementById(\'similarProductsModal\').remove()" style="background:#f8f9fa;border:none;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;color:#6c757d;transition:all 0.2s;" onmouseover="this.style.background=\'#e9ecef\';this.style.color=\'#5c2145\';" onmouseout="this.style.background=\'#f8f9fa\';this.style.color=\'#6c757d\';">×</button>';
  html += '</div>';
  
  if (similarProducts.length > 0) {
    html += '<div style="display:flex;flex-direction:column;gap:12px;">';
    for (let i = 0; i < similarProducts.length; i++) {
      const r = similarProducts[i];
      const p = r.product;
      const score = (r.similarity_score * 100).toFixed(1);
      const scoreColor = r.similarity_score > 0.7 ? '#28a745' : (r.similarity_score > 0.5 ? '#ffc107' : '#6c757d');
      const scoreLabel = r.similarity_score > 0.7 ? 'Very Similar' : (r.similarity_score > 0.5 ? 'Similar' : 'Somewhat Similar');
      
      html += `<div style="display:flex;gap:16px;padding:16px;background:linear-gradient(135deg,#f8f9fa 0%,#fff 100%);border:1px solid #e9ecef;border-radius:12px;transition:all 0.2s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.08)';this.style.transform='translateY(-2px)';this.style.borderColor='#5c2145';" onmouseout="this.style.boxShadow='none';this.style.transform='translateY(0)';this.style.borderColor='#e9ecef';">`;
      html += `<div style="flex:1;">`;
      html += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">`;
      html += `<span style="background:#5c2145;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;">${i + 1}</span>`;
      html += `<span style="font-weight:600;font-size:15px;color:#212529;">${p.name}</span>`;
      html += `<span style="background:#e9ecef;padding:3px 10px;border-radius:20px;font-size:11px;color:#5c2145;">${p.category}</span>`;
      html += `</div>`;
      html += `<p style="color:#6c757d;font-size:13px;margin:0 0 8px 0;line-height:1.5;">${p.description || 'No description available'}</p>`;
      html += `<div style="display:flex;align-items:center;gap:12px;font-size:13px;">`;
      html += `<span style="color:#5c2145;font-weight:500;">${p.brand}</span>`;
      html += `<span style="color:#dee2e6;">|</span>`;
      html += `<span style="font-weight:600;color:#212529;">₹${p.price.toFixed(2)}</span>`;
      html += `</div>`;
      html += `</div>`;
      html += `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:90px;padding-left:16px;border-left:2px solid #e9ecef;">`;
      html += `<div style="font-size:28px;font-weight:700;color:${scoreColor};text-shadow:0 2px 4px rgba(0,0,0,0.1);">${score}<span style="font-size:14px;">%</span></div>`;
      html += `<div style="font-size:11px;color:#6c757d;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">${scoreLabel}</div>`;
      html += `</div>`;
      html += `</div>`;
    }
    html += '</div>';
  } else {
    html += '<div style="text-align:center;padding:40px;">';
    html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:56px;height:56px;margin-bottom:16px;color:#dee2e6;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="21.17" y1="4.83" x2="16.66" y2="9.34"/><line x1="7.34" y1="14.66" x2="2.83" y2="19.17"/></svg>';
    html += '<p style="color:#6c757d;font-size:15px;margin:0;">No similar products found.</p>';
    if (allSimilarProducts.length > 0 && similarProducts.length === 0) {
      html += `<p style="color:#adb5bd;font-size:13px;margin-top:8px;">Found ${allSimilarProducts.length} products but none met the ${(SIMILARITY_THRESHOLD * 100).toFixed(0)}% similarity threshold.</p>`;
    } else {
      html += '<p style="color:#adb5bd;font-size:13px;margin-top:8px;">Try with a different product.</p>';
    }
    html += '</div>';
  }
  
  html += '</div>';
  modal.innerHTML = html;
  document.body.appendChild(modal);
  
  modal.addEventListener('click', function(e) {
    if (e.target === modal) modal.remove();
  });
  
  document.addEventListener('keydown', function closeOnEsc(e) {
    if (e.key === 'Escape') {
      modal.remove();
      document.removeEventListener('keydown', closeOnEsc);
    }
  });
}

function toggleHelpDropdown() {
  const dropdown = document.getElementById('helpDropdown');
  if (dropdown.style.display === 'none' || !dropdown.style.display) {
    dropdown.style.display = 'block';
    dropdown.style.animation = 'fadeSlideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1) both';
  } else {
    dropdown.style.display = 'none';
  }
}

function showPolicyModal(productId) {
  const product = products.find(p => p.id === productId);
  if (!product || !product.policy) return;
  
  const modal = document.createElement('div');
  modal.id = 'policyModal';
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:1000;display:flex;align-items:center;justify-content:center;';
  
  let html = '<div style="background:#fff;border-radius:12px;padding:24px;max-width:500px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:slideUp 0.3s ease-out;">';
  html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #e9ecef;">';
  html += `<h3 style="margin:0;color:#5c2145;">${product.name} - Policy Information</h3>`;
  html += '<button onclick="document.getElementById(\'policyModal\').remove()" style="background:#f8f9fa;border:none;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;color:#6c757d;">×</button>';
  html += '</div>';
  
  html += '<div style="display:flex;flex-direction:column;gap:16px;">';
  html += `<div style="padding:12px;background:#f8f9fa;border-radius:8px;"><strong style="color:#5c2145;display:block;margin-bottom:4px;">Warranty Period</strong><span style="color:#495057;">${product.policy.warranty_period || 'Not specified'}</span></div>`;
  html += `<div style="padding:12px;background:#f8f9fa;border-radius:8px;"><strong style="color:#5c2145;display:block;margin-bottom:4px;">Return Window</strong><span style="color:#495057;">${product.policy.return_window || 'Not specified'}</span></div>`;
  html += `<div style="padding:12px;background:#f8f9fa;border-radius:8px;"><strong style="color:#5c2145;display:block;margin-bottom:4px;">Refund Policy</strong><span style="color:#495057;">${product.policy.refund_policy || 'Not specified'}</span></div>`;
  if (product.policy.vendor_faq_link) {
    html += `<div style="padding:12px;background:#f8f9fa;border-radius:8px;"><strong style="color:#5c2145;display:block;margin-bottom:4px;">Vendor FAQ</strong><a href="${product.policy.vendor_faq_link}" target="_blank" style="color:#5c2145;">${product.policy.vendor_faq_link}</a></div>`;
  }
  html += '</div>';
  html += '</div>';
  
  modal.innerHTML = html;
  document.body.appendChild(modal);
  
  modal.addEventListener('click', function(e) {
    if (e.target === modal) modal.remove();
  });
}

let isRagChatOpen = false;
let isRagSidebarOpen = true;
let ragChats = [];
let currentRagChatId = null;
let mongoChatIds = {}
let quoteAgentChatId = null;

async function loadRagChats() {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/rag/chats/', {
      headers: { 'X-CSRFToken': csrfToken }
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.chats.length > 0) {
        ragChats = data.chats.map(chat => ({
          id: chat.id,
          title: chat.title,
          messages: chat.messages,
          createdAt: chat.created_at,
          updatedAt: chat.updated_at
        }));
        saveRagChatsToLocal();
        renderRagChatList();
        if (ragChats.length > 0 && !currentRagChatId) {
          loadRagChat(ragChats[0].id);
        }
        return;
      }
    }
  } catch (e) {
    console.log('Failed to load from MongoDB, falling back to localStorage');
  }
  
  const stored = localStorage.getItem('ragChats');
  if (stored) {
    ragChats = JSON.parse(stored);
    renderRagChatList();
    syncChatsToMongoDB();
  }
}

function saveRagChatsToLocal() {
  localStorage.setItem('ragChats', JSON.stringify(ragChats));
}

async function syncChatsToMongoDB() {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/rag/chats/sync/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ chats: ragChats })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Synced', data.synced_count, 'chats to MongoDB');
      await loadRagChats();
    }
  } catch (e) {
    console.error('Failed to sync to MongoDB:', e);
  }
}

async function saveChatToMongo(chat) {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/rag/chats/' + chat.id + '/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        messages: chat.messages,
        title: chat.title
      })
    });
    return response.ok;
  } catch (e) {
    console.error('Failed to save chat to MongoDB:', e);
    return false;
  }
}

async function saveQuoteAgentChatToMongo(messages, title) {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/agent/chats/sync/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ chat_id: quoteAgentChatId, messages: messages, title: title })
    });
    if (response.ok) {
      const data = await response.json();
      if (data.chat_id) quoteAgentChatId = data.chat_id;
      if (data.chat && data.chat.id) quoteAgentChatId = data.chat.id;
    }
  } catch (e) {
    console.error('Failed to save quote agent chat to MongoDB:', e);
  }
}

function toggleRagChat() {
  const widget = document.getElementById('ragWidget');
  const trigger = document.getElementById('ragTrigger');
  isRagChatOpen = !isRagChatOpen;
  
  if (isRagChatOpen) {
    widget.style.display = 'flex';
    widget.classList.add('open');
    trigger.style.display = 'none';
    loadRagChats();
  } else {
    widget.classList.remove('open');
    setTimeout(() => {
      widget.style.display = 'none';
    }, 400);
    trigger.style.display = 'flex';
  }
  loadRagChats();
}

function toggleRagSidebar() {
  document.getElementById('ragSidebar').classList.toggle('expanded');
}

async function createNewRagChat() {
  const newChat = {
    id: Date.now().toString(),
    title: 'New Chat',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/rag/chats/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ title: newChat.title })
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        newChat.id = data.chat.id;
      }
    }
  } catch (e) {
    console.error('Failed to create chat in MongoDB:', e);
  }
  
  ragChats.unshift(newChat);
  saveRagChatsToLocal();
  currentRagChatId = newChat.id;
  renderRagChatList();
  loadRagChat(newChat.id);
}

function loadRagChat(chatId) {
  currentRagChatId = chatId;
  const chat = ragChats.find(c => c.id === chatId);
  if (!chat) return;
  
  document.getElementById('ragCurrentChatTitle').textContent = chat.title;
  
  const container = document.getElementById('ragChatMessages');
  container.innerHTML = '';
  
  if (chat.messages.length === 0) {
    const welcomeDiv = document.createElement('div');
    welcomeDiv.style.cssText = 'flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#64748b;padding:40px 20px;text-align:center;';
    welcomeDiv.innerHTML = `
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:#e2e8f0;margin-bottom:16px;">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4"/>
        <path d="M12 8h.01"/>
      </svg>
      <p style="font-size:15px;font-weight:500;color:#475569;margin-bottom:8px;">How can I help you today?</p>
      <p style="font-size:13px;color:#94a3b8;max-width:280px;">Ask about inventory, product details, policies, warranties, or return procedures.</p>
    `;
    container.appendChild(welcomeDiv);
  } else {
    chat.messages.forEach(msg => {
      addRagMessageToUI(msg.content, msg.role === 'user', msg.trace_url);
    });
  }
  
  renderRagChatList();
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#5c2145';
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${bgColor};
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
    animation: slideInRight 0.3s ease-out;
    display: flex;
    align-items: center;
    gap: 8px;
  `;
  
  const icon = type === 'success' 
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'
    : type === 'error'
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
  
  toast.innerHTML = `${icon}<span>${message}</span>`;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

async function deleteRagChat(chatId) {
  const chat = ragChats.find(c => c.id === chatId);
  const chatTitle = chat ? chat.title : 'Chat';
  
  try {
    const csrfToken = getCookie('csrftoken');
    await fetch('/rag/chats/' + chatId + '/', {
      method: 'DELETE',
      headers: { 'X-CSRFToken': csrfToken }
    });
  } catch (e) {
    console.error('Failed to delete from MongoDB:', e);
  }
  
  ragChats = ragChats.filter(c => c.id !== chatId);
  saveRagChatsToLocal();
  
  showToast(`"${chatTitle}" deleted`, 'success');
  
  if (currentRagChatId === chatId) {
    if (ragChats.length > 0) {
      loadRagChat(ragChats[0].id);
    } else {
      createNewRagChat();
    }
  }
  renderRagChatList();
}

function renderRagChatList() {
  const list = document.getElementById('ragChatList');
  if (ragChats.length === 0) {
    list.innerHTML = '<div style="padding: 20px; text-align: center; color: #64748b; font-size: 13px;">No chats yet</div>';
    return;
  }
  
  list.innerHTML = ragChats.map(chat => {
    const date = new Date(chat.updatedAt);
    const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const isActive = chat.id === currentRagChatId;
    const preview = chat.messages.length > 0 ? chat.messages[0].content.substring(0, 30) + '...' : 'No messages';
    
    return `
      <div class="history-item ${isActive ? 'active' : ''}" style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; cursor: pointer; transition: background .15s;" onclick="if(event.target.closest('.delete-btn')) return; loadRagChat('${chat.id}')">
        <div style="flex: 1; min-width: 0; overflow: hidden;">
          <div class="title">${chat.title}</div>
          <div class="preview">${preview}</div>
          <div class="time">${dateStr}</div>
        </div>
        <button class="delete-btn" onclick="deleteRagChat('${chat.id}')" 
                style="width: 24px; height: 24px; border: none; background: transparent; color: ${isActive ? 'rgba(255,255,255,0.7)' : '#94a3b8'}; 
                       cursor: pointer; border-radius: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; margin-left: 8px;"
                onmouseover="this.style.background='${isActive ? 'rgba(255,255,255,0.2)' : '#fee2e2'}'; this.style.color='${isActive ? '#fff' : '#dc2626'}';"
                onmouseout="this.style.background='transparent'; this.style.color='${isActive ? 'rgba(255,255,255,0.7)' : '#94a3b8'}';"
                title="Delete chat">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    `;
  }).join('');
}

function formatMarkdown(text) {
  // Convert bold: **text** → <strong>text</strong>
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Convert italics: *text* → <em>text</em> (but not inside already converted tags)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Convert bullet points: * Item or - Item → <li>Item</li>
  // Handle bullet lists
  const lines = formatted.split('\n');
  let inList = false;
  let result = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      if (!inList) {
        result.push('<ul style="margin: 8px 0; padding-left: 20px;">');
        inList = true;
      }
      const itemText = trimmed.substring(2);
      result.push(`<li style="margin: 4px 0; line-height: 1.5;">${itemText}</li>`);
    } else {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      if (trimmed === '') {
        result.push('<br>');
      } else {
        result.push(line);
      }
    }
  }
  if (inList) result.push('</ul>');
  
  return result.join('\n');
}

function addRagMessageToUI(text, isUser, traceUrl = null) {
  const container = document.getElementById('ragChatMessages');
  
  const row = document.createElement('div');
  row.className = 'msg-row ' + (isUser ? 'user' : 'bot');
  
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formatted = isUser ? text.replace(/\n/g, '<br>') : formatMarkdown(text);
  
  // Build trace link HTML if traceUrl is provided (only for bot messages)
  let traceLinkHtml = '';
  if (!isUser && traceUrl) {
    traceLinkHtml = `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;">
      <a href="${traceUrl}" target="_blank" rel="noopener noreferrer" 
         style="display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: #5c2145; text-decoration: none; font-weight: 500;"
         onmouseover="this.style.textDecoration='underline'" 
         onmouseout="this.style.textDecoration='none'">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/>
          <line x1="10" y1="14" x2="21" y2="3"/>
        </svg>
        View Trace in Langsmith
      </a>
    </div>`;
  }
  
  if (isUser) {
    row.innerHTML = `<div class="bubble">${formatted}<span class="timestamp">${time}</span></div>`;
  } else {
    row.innerHTML = `<div class="bot-avatar" style="display:flex;align-items:center;justify-content:center;"><img src="${window.ICON_URL}" alt="Rippling" style="width:22px;height:22px;object-fit:contain;border-radius:5px;"></div><div class="bubble" style="line-height: 1.6;">${formatted}${traceLinkHtml}<span class="timestamp">${time}</span></div>`;
  }
  
  row.style.animationDuration = '0.25s';
  container.appendChild(row);
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

async function generateChatTitle(firstMessage) {
  try {
    const csrfToken = getCookie('csrftoken');
    const response = await fetch('/rag/generate-title/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ message: firstMessage })
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        return data.title;
      }
    }
    const words = firstMessage.split(' ').slice(0, 5);
    let title = words.join(' ');
    if (firstMessage.split(' ').length > 5) title += '...';
    return title || 'New Chat';
  } catch (e) {
    const words = firstMessage.split(' ').slice(0, 5);
    let title = words.join(' ');
    if (firstMessage.split(' ').length > 5) title += '...';
    return title || 'New Chat';
  }
}

function detectQuoteIntent(text) {
  const quoteKeywords = [
    'quote', 'price', 'cost', 'discount', 'deal', 'bulk', 'order',
    'how much', 'total', 'invoice', 'pricing', 'quantity', 'units',
    'purchase', 'buy', 'get a quote', 'best price', 'wholesale'
  ];
  const lowerText = text.toLowerCase();
  return quoteKeywords.some(keyword => lowerText.includes(keyword));
}

function formatQuoteResponse(data) {
  if (!data.quote) return data.response || 'No quote data available.';
  
  const q = data.quote;
  let html = `<div style="background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%); border: 2px solid #5c2145; border-radius: 12px; padding: 16px; margin: 8px 0;">`;
  html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">`;
  html += `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5c2145" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
  html += `<span style="font-weight: 700; color: #5c2145; font-size: 16px;">Quote Generated</span>`;
  html += `</div>`;
  
  html += `<div style="background: white; border-radius: 8px; padding: 12px; margin-bottom: 12px; border: 1px solid #e2e8f0;">`;
  html += `<div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">${q.product_name}</div>`;
  html += `<div style="font-size: 12px; color: #64748b;">Product ID: ${q.product_id}</div>`;
  html += `</div>`;
  
  html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">`;
  html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e2e8f0;">`;
  html += `<div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Quantity</div>`;
  html += `<div style="font-size: 18px; font-weight: 700; color: #5c2145;">${q.quantity}</div>`;
  html += `</div>`;
  html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center; border: 1px solid #e2e8f0;">`;
  html += `<div style="font-size: 11px; color: #64748b; text-transform: uppercase;">Unit Price</div>`;
  html += `<div style="font-size: 18px; font-weight: 700; color: #5c2145;">₹${q.unit_price}</div>`;
  html += `</div>`;
  html += `</div>`;
  
  if (q.discount_pct > 0) {
    html += `<div style="background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border: 1px solid #86efac; border-radius: 8px; padding: 12px; margin-bottom: 12px;">`;
    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">`;
    html += `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`;
    html += `<span style="font-weight: 600; color: #16a34a;">${q.discount_pct}% Discount Applied!</span>`;
    html += `</div>`;
    html += `<div style="font-size: 12px; color: #166534;">You save ₹${q.discount_amount}</div>`;
    html += `</div>`;
  }
  
  html += `<div style="background: linear-gradient(135deg, #5c2145 0%, #8b3a5c 100%); border-radius: 8px; padding: 12px; color: white;">`;
  html += `<div style="display: flex; justify-content: space-between; align-items: center;">`;
  html += `<span style="font-size: 12px; opacity: 0.9;">Subtotal</span>`;
  html += `<span style="font-weight: 500;">₹${q.subtotal}</span>`;
  html += `</div>`;
  if (q.discount_amount > 0) {
    html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">`;
    html += `<span style="font-size: 12px; opacity: 0.9;">Discount</span>`;
    html += `<span style="font-weight: 500; color: #86efac;">-₹${q.discount_amount}</span>`;
    html += `</div>`;
  }
  html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);">`;
  html += `<span style="font-weight: 600;">Total</span>`;
  html += `<span style="font-size: 20px; font-weight: 700;">₹${q.total}</span>`;
  html += `</div>`;
  html += `</div>`;
  
  html += `</div>`;
  return html;
}

async function sendRagMessage() {
  const input = document.getElementById('ragInput');
  const sendBtn = document.getElementById('ragSendBtn');
  const text = input.value.trim();
  if (!text) return;

  // Show message and lock input immediately — before any async work.
  addRagMessageToUI(text, true);
  input.value = '';
  if (sendBtn) sendBtn.disabled = true;

  if (!currentRagChatId) {
    await createNewRagChat();
  }

  const chat = ragChats.find(c => c.id === currentRagChatId);
  if (!chat) return;

  chat.messages.push({role: 'user', content: text});
  chat.updatedAt = new Date().toISOString();

  // Title generation and mongo sync run in the background — don't block the UI.
  if (chat.messages.length === 1) {
    generateChatTitle(text).then(title => {
      if (title) {
        chat.title = title;
        document.getElementById('ragCurrentChatTitle').textContent = title;
        renderRagChatList();
      }
    });
  }
  await saveQuoteAgentChatToMongo(chat.messages, chat.title);

  const container = document.getElementById('ragChatMessages');
  
  // Create minimal Claude-style thinking indicator
  const reasoningDiv = document.createElement('div');
  reasoningDiv.id = 'ragReasoning';
  reasoningDiv.className = 'msg-row bot';
  reasoningDiv.style.cssText = 'align-items: flex-start;';
  reasoningDiv.innerHTML = `
    <div class="bot-avatar" style="display:flex;align-items:center;justify-content:center;margin-top:2px;"><img src="${window.ICON_URL}" alt="R" style="width:22px;height:22px;object-fit:contain;border-radius:5px;"></div>
    <div style="display:flex;flex-direction:column;gap:6px;max-width:85%;">
      <div class="thinking-pill" style="display:inline-flex;align-items:center;gap:7px;padding:5px 11px;background:#f1f5f9;border-radius:20px;width:fit-content;">
        <span class="thinking-dots" style="display:flex;gap:3px;align-items:center;">
          <span style="width:5px;height:5px;border-radius:50%;background:#5c2145;opacity:0.9;animation:ragDot 1.4s ease-in-out infinite;animation-delay:0s;display:inline-block;"></span>
          <span style="width:5px;height:5px;border-radius:50%;background:#5c2145;opacity:0.9;animation:ragDot 1.4s ease-in-out infinite;animation-delay:0.2s;display:inline-block;"></span>
          <span style="width:5px;height:5px;border-radius:50%;background:#5c2145;opacity:0.9;animation:ragDot 1.4s ease-in-out infinite;animation-delay:0.4s;display:inline-block;"></span>
        </span>
        <span class="reasoning-status" style="font-size:12px;color:#5c2145;font-weight:500;letter-spacing:0.01em;">Thinking</span>
        <span class="reasoning-timer" style="font-size:11px;color:#94a3b8;font-variant-numeric:tabular-nums;min-width:28px;">0s</span>
      </div>
      <div class="reasoning-content" style="display:none;">
        <!-- Final response will appear here -->
      </div>
    </div>
  `;
  container.appendChild(reasoningDiv);
  container.scrollTop = container.scrollHeight;

  const statusEl = reasoningDiv.querySelector('.reasoning-status');
  const timerEl = reasoningDiv.querySelector('.reasoning-timer');
  const contentEl = reasoningDiv.querySelector('.reasoning-content');
  const pillEl = reasoningDiv.querySelector('.thinking-pill');

  // Timer
  let _timerSecs = 0;
  const _timerInterval = setInterval(() => {
    _timerSecs++;
    timerEl.textContent = _timerSecs + 's';
  }, 1000);

  const steps = {};

  function addStep(stepId, stepName, status = 'pending') {
    // Just update the pill label — no visual step rows
    steps[stepId] = { stepName, status };
    return steps[stepId];
  }

  function updateStep(stepId, status, detail = '') {
    if (!steps[stepId]) return;
    steps[stepId].status = status;
    // Show the last active step name in the pill
    if (status === 'active') {
      statusEl.textContent = steps[stepId].stepName;
    }
  }
  
  try {
    const csrfToken = getCookie('csrftoken');
    
    const response = await fetch('/agent/chat/stream/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        message: text,
        chat_history: chat.messages.slice(-10),
        chat_id: quoteAgentChatId,
        title: chat.title
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalData = null;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            
            if (event.type === 'step') {
              const stepId = event.step.toLowerCase().replace(/\s+/g, '-');
              const stepName = event.step;
              
              if (!steps[stepId]) {
                steps[stepId] = addStep(stepId, stepName, 'active');
              }
              
              // Mark previous steps as completed
              const stepIds = Object.keys(steps);
              const currentIndex = stepIds.indexOf(stepId);
              for (let i = 0; i < currentIndex; i++) {
                updateStep(stepIds[i], 'completed');
              }
              
              updateStep(stepId, 'active', event.message);
              statusEl.textContent = event.message;
              
              container.scrollTop = container.scrollHeight;
            }
            else if (event.type === 'result') {
              // Mark all steps as completed
              Object.keys(steps).forEach(stepId => updateStep(stepId, 'completed'));
              
              finalData = event.data;
              const isQuoteQuery = detectQuoteIntent(text);
              
              let responseText;
              if (isQuoteQuery && finalData.quote) {
                responseText = formatQuoteResponse(finalData);
              } else {
                responseText = finalData.response || 'No response available.';
              }
              
              // Stop timer, freeze pill as "Done · Xs"
              clearInterval(_timerInterval);
              pillEl.style.background = '#f0fdf4';
              pillEl.querySelector('.thinking-dots').innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';
              statusEl.style.color = '#16a34a';
              statusEl.textContent = 'Done';
              timerEl.textContent = '· ' + _timerSecs + 's';

              // Show final response below the pill in a proper bubble
              contentEl.style.display = 'block';
              contentEl.style.cssText = 'display:block;background:white;border:1px solid #e2e8f0;border-radius:12px;padding:12px 14px;font-size:13px;line-height:1.65;color:#1e293b;margin-top:4px;';
              contentEl.innerHTML = formatMarkdown(responseText);
              
              if (finalData.trace_id) {
                const traceLink = document.createElement('div');
                traceLink.style.cssText = 'margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0;';
                traceLink.innerHTML = `
                  <a href="https://smith.langchain.com/traces/${finalData.trace_id}" target="_blank" rel="noopener noreferrer" 
                     style="display: inline-flex; align-items: center; gap: 6px; font-size: 11px; color: #5c2145; text-decoration: none; font-weight: 500;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                      <polyline points="15 3 21 3 21 9"/>
                      <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                    View Trace
                  </a>
                `;
                contentEl.appendChild(traceLink);
              }
              
              // Save to chat history
              chat.messages.push({
                role: 'assistant',
                content: responseText,
                trace_url: finalData.trace_id ? `https://smith.langchain.com/traces/${finalData.trace_id}` : null
              });
              chat.updatedAt = new Date().toISOString();

              await saveQuoteAgentChatToMongo(chat.messages, chat.title);
            }
            else if (event.type === 'error') {
              const activeStep = Object.keys(steps).find(id => steps[id].status === 'active');
              if (activeStep) {
                updateStep(activeStep, 'error', event.error);
              }
              
              clearInterval(_timerInterval);
              pillEl.style.background = '#fef2f2';
              pillEl.querySelector('.thinking-dots').innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
              statusEl.style.color = '#ef4444';
              statusEl.textContent = 'Error';
              timerEl.textContent = '';
              
              contentEl.style.display = 'block';
              contentEl.style.cssText = 'display:block;background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:10px 14px;font-size:13px;color:#ef4444;margin-top:4px;';
              contentEl.innerHTML = `Error: ${event.error}`;
              
              chat.messages.push({role: 'assistant', content: `Error: ${event.error}`});
              chat.updatedAt = new Date().toISOString();
              await saveQuoteAgentChatToMongo(chat.messages, chat.title);
            }
            else if (event.type === 'saved') {
              quoteAgentChatId = event.chat_id;
            }
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
    
    container.scrollTop = container.scrollHeight;
    
  } catch (e) {
    clearInterval(_timerInterval);
    const reasoningEl = document.getElementById('ragReasoning');
    if (reasoningEl) {
      reasoningEl.remove();
    }
    
    let errorMsg = 'Failed to get response. Please check your connection.';
    if (e.name === 'AbortError') {
      errorMsg = 'Request timed out. The AI service is taking too long to respond. Please try again.';
    } else if (e.message.includes('Failed to fetch')) {
      errorMsg = 'Network error. Please check your internet connection and try again.';
    } else if (e.message.includes('CSRF')) {
      errorMsg = 'Security error. Please refresh the page and try again.';
    }
    addRagMessageToUI(errorMsg, false);
    
    chat.messages.push({role: 'assistant', content: errorMsg});
    chat.updatedAt = new Date().toISOString();
    await saveQuoteAgentChatToMongo(chat.messages, chat.title);
  } finally {
    const sb = document.getElementById('ragSendBtn');
    const ri = document.getElementById('ragInput');
    if (sb) sb.disabled = !ri?.value.trim();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  loadRagChats();
  loadAiChats();
  
  const ragInput = document.getElementById('ragInput');
  const ragSendBtn = document.getElementById('ragSendBtn');
  if (ragInput && ragSendBtn) {
    ragInput.addEventListener('input', function() {
      ragSendBtn.disabled = !this.value.trim();
    });
    ragSendBtn.disabled = !ragInput.value.trim();
  }

  const aiInput = document.getElementById('scenarioInput');
  const aiSendBtn = document.getElementById('aiSendBtn');
  if (aiInput && aiSendBtn) {
    aiInput.addEventListener('input', function() {
      aiSendBtn.disabled = !this.value.trim();
    });
    aiSendBtn.disabled = !aiInput.value.trim();
  }
});

