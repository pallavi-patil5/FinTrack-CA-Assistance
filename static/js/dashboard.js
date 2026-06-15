const API="";
let chartInstance=null;

async function apiPost(path,body){
  const r=await fetch(API+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  if(!r.ok){
    const err=await r.text();
    throw new Error(`HTTP ${r.status}: ${err}`);
  }
  return r.json();
}

document.addEventListener('DOMContentLoaded',()=>{
  if(typeof lucide!=='undefined')lucide.createIcons();
  load();loadInvoices();loadVendors();loadTransactions();
  loadReminderWidgets();
});

function show(id,el){
  document.querySelectorAll(".section").forEach(s=>{s.classList.remove("active");s.style.display="none";});
  const t=document.getElementById(id);if(!t)return;t.style.display="block";requestAnimationFrame(()=>t.classList.add("active"));
  document.querySelectorAll(".sidebar a").forEach(a=>a.classList.remove("active"));
  if(el) el.classList.add("active");
  const pt=document.getElementById("pageTitle");if(pt)pt.innerText=id.charAt(0).toUpperCase()+id.slice(1);
  if(id==="invoices")loadInvoices();if(id==="transactions")loadTransactions();if(id==="vendors")loadVendors();
}

function toggleTheme(){
  document.body.classList.toggle("dark");
  const icon=document.getElementById("themeIcon");
  if(icon){icon.setAttribute("data-lucide",document.body.classList.contains("dark")?"sun":"moon");if(typeof lucide!=='undefined')lucide.createIcons();}
}

function globalSearch(q){
  const active=document.querySelector(".section.active");if(!active)return;
  active.querySelectorAll("tbody tr").forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q.toLowerCase())?"":"none");
}

function showToast(msg,type="success"){
  const t=document.getElementById("toast");if(!t)return;
  document.getElementById("toastMsg").innerText=msg;
  t.className="toast "+type;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2800);
}

/* DASHBOARD */
let pieChartInstance=null;

async function load(){
  try{
    const [s, invData, txData] = await Promise.all([
      fetch(API+"/summary/admin").then(r=>r.json()),
      fetch(API+"/invoices/list/admin").then(r=>r.json()),
      fetch(API+"/transactions/admin").then(r=>r.json())
    ]);

    // ── SUMMARY CARDS ──────────────────────────────────
    const invoices = invData.invoices||[];
    const sum=document.getElementById("summary");if(!sum)return;
    sum.innerHTML=`
      <div class="stat-card"><div class="stat-icon emerald"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div><div class="stat-info"><h4>Total Income</h4><p>Rs.${parseFloat(s.total_income||0).toFixed(2)}</p></div></div>
      <div class="stat-card"><div class="stat-icon rose"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg></div><div class="stat-info"><h4>Total Expense</h4><p>Rs.${parseFloat(s.total_expense||0).toFixed(2)}</p></div></div>
      <div class="stat-card"><div class="stat-icon indigo"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg></div><div class="stat-info"><h4>Net Balance</h4><p>Rs.${parseFloat(s.net_balance||0).toFixed(2)}</p></div></div>
      <div class="stat-card"><div class="stat-icon amber"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="stat-info"><h4>Total Invoices</h4><p>${invoices.length}</p></div></div>`;

    // ── LINE CHART (monthly trend) ──────────────────────
    const txns = txData.transactions||[];
    const months={};
    txns.forEach(t=>{
      const m=t.date?t.date.slice(0,7):'Unknown';
      if(!months[m])months[m]={income:0,expense:0};
      if(t.type==='Income')months[m].income+=parseFloat(t.amount||0);
      else months[m].expense+=parseFloat(t.amount||0);
    });
    const labels=Object.keys(months).sort();
    const incomeData=labels.map(m=>months[m].income);
    const expenseData=labels.map(m=>months[m].expense);

    if(chartInstance)chartInstance.destroy();
    const ctx=document.getElementById("chart");if(ctx){
      chartInstance=new Chart(ctx.getContext("2d"),{
        type:'line',
        data:{
          labels:labels.length?labels:['No Data'],
          datasets:[
            {label:'Income',data:incomeData,borderColor:'#10b981',backgroundColor:'rgba(16,185,129,0.08)',tension:.4,fill:true,pointRadius:4,pointBackgroundColor:'#10b981'},
            {label:'Expense',data:expenseData,borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,0.08)',tension:.4,fill:true,pointRadius:4,pointBackgroundColor:'#ef4444'}
          ]
        },
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'}},scales:{y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'}},x:{grid:{display:false}}}}
      });
    }

    // ── PIE CHART (invoice status) ──────────────────────
    const paid=invoices.filter(i=>(i.status||'').toLowerCase()==='paid').length;
    const pending=invoices.filter(i=>(i.status||'').toLowerCase()==='pending').length;
    const overdue=invoices.filter(i=>(i.status||'').toLowerCase()==='overdue').length;
    const other=invoices.length-paid-pending-overdue;
    if(pieChartInstance)pieChartInstance.destroy();
    const pctx=document.getElementById("pieChart");if(pctx){
      pieChartInstance=new Chart(pctx.getContext("2d"),{
        type:'doughnut',
        data:{
          labels:['Paid','Pending','Overdue','Other'],
          datasets:[{data:[paid,pending,overdue,other],backgroundColor:['#10b981','#f59e0b','#ef4444','#94a3b8'],borderWidth:0,hoverOffset:6}]
        },
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,padding:12,font:{size:11}}}}}
      });
    }

    // ── RECENT INVOICES ─────────────────────────────────
    const ri=document.getElementById("recentInvoices");if(ri){
      const recent=invoices.slice(-5).reverse();
      ri.innerHTML=recent.length?recent.map(i=>{
        const st=(i.status||'pending').toLowerCase();
        return `<tr onclick="openInvoicePanel('${i._id}')" style="cursor:pointer"><td>${i.vendor_name}</td><td class="amount">Rs.${parseFloat(i.total_amount||0).toFixed(2)}</td><td><span class="badge ${st}">${i.status||'Pending'}</span></td></tr>`;
      }).join(''):'<tr><td colspan="3" style="text-align:center;color:var(--text-secondary);padding:20px">No invoices yet</td></tr>';
    }

    // ── RECENT TRANSACTIONS ─────────────────────────────
    const rt=document.getElementById("recentTxns");if(rt){
      const recent=txns.slice(0,5);
      rt.innerHTML=recent.length?recent.map(t=>`<tr><td><span class="badge ${t.type==='Income'?'paid':'rose'}">${t.type}</span></td><td class="amount">Rs.${parseFloat(t.amount||0).toFixed(2)}</td><td>${t.category||'-'}</td></tr>`).join(''):'<tr><td colspan="3" style="text-align:center;color:var(--text-secondary);padding:20px">No transactions yet</td></tr>';
    }

  }catch(e){console.error(e)}
}

/* TRANSACTIONS */
async function loadTransactions(){
  try{
    const tx=await fetch(API+"/transactions/admin").then(r=>r.json());
    const tb=document.getElementById("txnTable");if(!tb)return;
    tb.innerHTML=tx.transactions.map(t=>{
      const cat=(t.category||'').replace(/'/g,"&#39;");
      const note=(t.note||'').replace(/'/g,"&#39;");
      return `<tr>
        <td><span class="badge ${t.type==='Income'?'paid':'rose'}">${t.type}</span></td>
        <td class="amount">Rs.${parseFloat(t.amount||0).toFixed(2)}</td>
        <td>${t.category||'-'}</td>
        <td>${t.note||'-'}</td>
        <td>${t.date||'-'}</td>
        <td style="text-align:center;min-width:140px;white-space:nowrap;" onclick="event.stopPropagation()">
          <div style="display:flex;gap:6px;justify-content:center;">
            <button class="txn-btn edit" title="Edit Transaction" onclick="openEditTxnModal('${t._id}','${t.type}',${t.amount},'${cat}','${note}')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Edit
            </button>
            <button class="txn-btn delete" title="Delete Transaction" onclick="deleteTxn('${t._id}')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
              Delete
            </button>
          </div>
        </td>
      </tr>`;
    }).join('');
  }catch(e){console.error(e)}
}

function openTxnModal(){document.getElementById("txnModal").classList.add("open");}
function closeTxnModal(){document.getElementById("txnModal").classList.remove("open");}

function openEditTxnModal(id, type, amount, category, note){
  document.getElementById("editTxnId").value = id;
  document.getElementById("editTxnType").value = type;
  document.getElementById("editTxnAmount").value = amount;
  document.getElementById("editTxnCategory").value = category;
  document.getElementById("editTxnNote").value = note;
  document.getElementById("editTxnModal").classList.add("open");
}
function closeEditTxnModal(){document.getElementById("editTxnModal").classList.remove("open");}

async function saveEditTxn(){
  const id=document.getElementById("editTxnId").value;
  const payload={
    type: document.getElementById("editTxnType").value,
    amount: parseFloat(document.getElementById("editTxnAmount").value||0),
    category: document.getElementById("editTxnCategory").value,
    note: document.getElementById("editTxnNote").value
  };
  if(!payload.amount||!payload.category){showToast("Amount and category required","error");return;}
  try{
    const r=await fetch(API+"/transactions/update/"+id,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    if(!r.ok)throw new Error("Failed");
    showToast("Transaction updated!");closeEditTxnModal();loadTransactions();load();
  }catch(e){showToast("Error updating","error");}
}

async function deleteTxn(id){
  if(!confirm("Delete this transaction?"))return;
  try{
    const r=await fetch(API+"/transactions/delete/"+id,{method:"DELETE"});
    if(!r.ok)throw new Error("Failed");
    showToast("Transaction deleted!");loadTransactions();load();
  }catch(e){showToast("Error deleting","error");}
}

async function submitTransaction(){
  const type=document.getElementById("txnType").value;
  const amount=parseFloat(document.getElementById("txnAmount").value||0);
  const category=document.getElementById("txnCategory").value;
  const note=document.getElementById("txnNote").value;
  if(!amount||!category){showToast("Amount and category required","error");return;}
  try{
    const r=await fetch(API+"/transactions/add",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({type,amount,category,note})});
    if(!r.ok)throw new Error("Failed");
    showToast("Transaction saved!");closeTxnModal();loadTransactions();load();
    document.getElementById("txnAmount").value="";document.getElementById("txnCategory").value="";document.getElementById("txnNote").value="";
  }catch(e){showToast("Error saving transaction","error");}
}

/* INVOICES */
let allInvoices = [];

async function uploadInvoice(){
  const file = document.getElementById("fileInput").files[0];
  if(!file) return;
  const sel = document.getElementById("invoiceTypeSelect");
  const invoiceType = sel ? sel.value : "incoming";
  console.log("[UPLOAD] invoice_type:", invoiceType);
  const fd = new FormData();
  fd.append("file", file);
  fd.append("invoice_type", invoiceType);
  showToast("Processing invoice...");
  try{
    const r = await fetch(API+"/upload-invoice", {method:"POST", body:fd});
    if(!r.ok){const err=await r.json();showToast("Upload failed: "+(err.detail||r.statusText),"error");return;}
    const data = await r.json();
    const inv = data.invoice||{};
    const txnType = invoiceType==="outgoing" ? "Income" : "Expense";
    const category = invoiceType==="outgoing" ? "Invoice Income" : "Invoice Expense";
    await fetch(API+"/transactions/add",{
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({type:txnType, amount:parseFloat(inv.total_amount||0), category, note:`Invoice - ${inv.vendor_name||'Unknown'}`})
    });
    showToast(`Invoice uploaded as ${txnType}!`);
    document.getElementById("fileInput").value="";
    await Promise.all([loadInvoices(), loadTransactions()]);
    load();
  }catch(e){showToast("Error: "+e.message,"error");}
}

async function loadInvoices(){
  try{
    const d=await fetch(API+"/invoices/list/admin").then(r=>r.json());
    allInvoices=d.invoices||[];
    applyInvFilters();
  }catch(e){console.error(e)}
}

function applyInvFilters(){
  const search=(document.getElementById("invSearch")?.value||"").toLowerCase();
  const status=document.getElementById("invStatus")?.value||"";
  const type=document.getElementById("invType")?.value||"";
  const filtered=allInvoices.filter(i=>{
    if(search&&!i.vendor_name.toLowerCase().includes(search))return false;
    if(status&&(i.status||"Pending")!==status)return false;
    if(type&&(i.invoice_type||"incoming")!==type)return false;
    return true;
  });
  renderInvStats(filtered);
  renderInvoiceTable(filtered);
}

function clearInvFilters(){
  ["invSearch"].forEach(id=>{const el=document.getElementById(id);if(el)el.value="";});
  ["invStatus","invType"].forEach(id=>{const el=document.getElementById(id);if(el)el.value="";});
  applyInvFilters();
}

function renderInvStats(invoices){
  const el=document.getElementById("invStats");if(!el)return;
  const total=invoices.length;
  const paid=invoices.filter(i=>(i.status||'').toLowerCase()==='paid').length;
  const pending=invoices.filter(i=>(i.status||'').toLowerCase()==='pending').length;
  const overdue=invoices.filter(i=>(i.status||'').toLowerCase()==='overdue').length;
  const amt=invoices.reduce((s,i)=>s+(parseFloat(i.total_amount)||0),0);
  el.innerHTML=`
    <div class="inv-stat total">Total <span>${total}</span></div>
    <div class="inv-stat total">Amount <span>Rs.${amt.toFixed(2)}</span></div>
    <div class="inv-stat paid">Paid <span>${paid}</span></div>
    <div class="inv-stat pending">Pending <span>${pending}</span></div>
    <div class="inv-stat overdue">Overdue <span>${overdue}</span></div>`;
}

function renderInvoiceTable(invoices){
  const tb=document.getElementById("invTable");if(!tb)return;
  if(invoices.length===0){tb.innerHTML='<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-secondary)">No invoices match the filters</td></tr>';return;}
  tb.innerHTML=invoices.map(i=>{
    const st=(i.status||'pending').toLowerCase();
    const catCls=(i.category||'Expense').toLowerCase();
    const amt=parseFloat(i.total_amount)||0;
    return `<tr onclick="openInvoicePanel('${i._id}')"><td>${i.vendor_name}</td><td class="amount">Rs.${amt.toFixed(2)}</td><td>${i.date||'-'}</td><td>${i.due_date&&i.due_date!=='None'?i.due_date:'-'}</td><td><span class="badge ${st}">${i.status||'Pending'}</span></td><td><span class="badge ${catCls}">${i.category||'Expense'}</span></td></tr>`;
  }).join('');
}

async function openInvoicePanel(id){
  try{
    const d=await fetch(API+"/invoice/detail/"+id).then(r=>r.json());
    const st=(d.status||'pending').toLowerCase();
    const catCls=(d.category||'Expense').toLowerCase();
    document.getElementById("invoicePanelContent").innerHTML=`
      <div class="detail-row"><span class="detail-label">Vendor</span><span class="detail-val">${d.vendor_name}</span></div>
      <div class="detail-row"><span class="detail-label">Amount</span><span class="detail-val">Rs.${parseFloat(d.total_amount).toFixed(2)}</span></div>
      <div class="detail-row"><span class="detail-label">Date</span><span class="detail-val">${d.date||'-'}</span></div>
      <div class="detail-row"><span class="detail-label">Due Date</span><span class="detail-val">${d.due_date!=='None'?d.due_date:'-'}</span></div>
      <div class="detail-row"><span class="detail-label">Status</span><span class="badge ${st}">${d.status||'Pending'}</span></div>
      <div class="detail-row"><span class="detail-label">Invoice Type</span><span class="detail-val">${d.invoice_type||'Incoming'}</span></div>
      <div class="detail-row"><span class="detail-label">Category</span><span class="badge ${catCls}">${d.category||'Expense'}</span></div>`;
    document.getElementById("invoicePanel").classList.add("open");
  }catch(e){console.error(e)}
}

/* VENDORS */
async function loadVendors(){
  try{
    const vendors=await fetch(API+"/vendors").then(r=>r.json());
    const totalVendors=vendors.length;
    const totalAmt=vendors.reduce((s,v)=>s+(v.total_amount||0),0);
    const totalInv=vendors.reduce((s,v)=>s+(v.total_invoices||0),0);
    const vc=document.getElementById("vendorCards");if(vc)vc.innerHTML=`
      <div class="stat-card"><div class="stat-icon blue"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div class="stat-info"><h4>Total Vendors</h4><p>${totalVendors}</p></div>
      <div class="stat-card"><div class="stat-icon indigo"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="stat-info"><h4>Total Invoices</h4><p>${totalInv}</p></div>
      <div class="stat-card"><div class="stat-icon emerald"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div><div class="stat-info"><h4>Total Amount</h4><p>Rs.${totalAmt.toFixed(2)}</p></div>`;
    const vt=document.getElementById("vendorTable");if(!vt)return;
    vt.innerHTML=vendors.map(v=>`<tr onclick="openVendorPanel('${v.vendor_id}','${v.name.replace(/'/g,"\\'")}')"><td>${v.name}</td><td>${v.total_invoices}</td><td class="amount">Rs.${(v.total_amount||0).toFixed(2)}</td><td id="pend_${v.vendor_id}">-</td><td id="over_${v.vendor_id}">-</td></tr>`).join('');
    vendors.forEach(v=>loadVendorCounts(v.vendor_id));
  }catch(e){console.error(e)}
}

async function loadVendorCounts(vid){
  try{
    const d=await fetch(API+`/vendor/${vid}/detail`).then(r=>r.json());
    const p=document.getElementById(`pend_${vid}`);const o=document.getElementById(`over_${vid}`);
    if(p)p.innerText=d.pending;if(o)o.innerText=d.overdue;
  }catch(e){}
}

async function openVendorPanel(vid,name){
  try{
    const d=await fetch(API+`/vendor/${vid}/detail`).then(r=>r.json());
    document.getElementById("vendorPanelName").innerText=name;
    const invRows=d.invoices.map(i=>{
      const st=(i.status||'pending').toLowerCase();
      const catCls=(i.category||'Expense').toLowerCase();
      return `<tr onclick="window.location.href='/invoice/${i.id}'"><td class="amount">Rs.${parseFloat(i.amount||0).toFixed(2)}</td><td><span class="badge ${st}">${i.status}</span></td><td>${i.date||'-'}</td><td><span class="badge ${catCls}">${i.category}</span></td></tr>`;
    }).join('');
    document.getElementById("vendorPanelContent").innerHTML=`
      <div class="detail-row"><span class="detail-label">Total Invoices</span><span class="detail-val">${d.total_invoices}</span></div>
      <div class="detail-row"><span class="detail-label">Total Amount</span><span class="detail-val">Rs.${parseFloat(d.total_amount||0).toFixed(2)}</span></div>
      <div class="detail-row"><span class="detail-label">Avg Amount</span><span class="detail-val">Rs.${parseFloat(d.avg_amount||0).toFixed(2)}</span></div>
      <div class="detail-row"><span class="detail-label">Pending</span><span class="detail-val">${d.pending}</span></div>
      <div class="detail-row"><span class="detail-label">Overdue</span><span class="detail-val">${d.overdue}</span></div>
      <div class="detail-row vendor-email-row">
        <span class="detail-label">Vendor Email</span>
        <div class="vendor-email-edit">
          <input id="vendorEmailInput" type="email" placeholder="vendor@example.com" value="${d.email||''}">
          <button class="btn btn-primary btn-sm" onclick="saveVendorEmail('${vid}')">Save</button>
        </div>
      </div>
      <h4 style="margin-top:16px;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--text-secondary)">Invoices</h4>
      <table class="vendor-inv-table"><thead><tr><th>Amount</th><th>Status</th><th>Date</th><th>Type</th></tr></thead><tbody>${invRows}</tbody></table>`;
    document.getElementById("vendorPanel").classList.add("open");
  }catch(e){console.error(e)}
}

async function saveVendorEmail(vid){
  const email=document.getElementById("vendorEmailInput")?.value?.trim();
  if(!email){showToast("Enter a valid email","error");return;}
  try{
    const r=await fetch(API+`/vendor/${vid}/email`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({email})});
    if(!r.ok)throw new Error("Failed");
    showToast("Vendor email saved!");
  }catch(e){showToast("Error saving email","error");}
}

function closePanel(id){document.getElementById(id).classList.remove("open");}

/* FINANCE TABS */
function showFinanceTab(tab,btn){
  document.querySelectorAll(".finance-tab-content").forEach(t=>t.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b=>b.classList.remove("active"));
  document.getElementById("tab-"+tab).classList.add("active");
  btn.classList.add("active");
}

function fmtResultCard(label,value){return`<div class="result-card"><h4>${label}</h4><div class="result-value">${value}</div></div>`;}

async function calcROI(){
  const inv=parseFloat(document.getElementById("roiInv").value||0);
  const profit=parseFloat(document.getElementById("roiProfit").value||0);
  if(!inv){showToast("Enter investment","error");return;}
  try{
    const d=await apiPost("/calculate/roi",{investment:inv,net_profit:profit});
    document.getElementById("roiResult").innerHTML=fmtResultCard("ROI",d.roi_percent+"%");
  }catch(e){console.error(e);showToast("Error: "+e.message,"error");}
}
async function calcMargin(){
  const rev=parseFloat(document.getElementById("mRevenue").value||0);
  const cost=parseFloat(document.getElementById("mCost").value||0);
  if(!rev){showToast("Enter revenue","error");return;}
  try{
    const d=await apiPost("/calculate/margin",{revenue:rev,cost});
    document.getElementById("marginResult").innerHTML=fmtResultCard("Gross Margin",d.gross_margin_percent+"%");
  }catch(e){console.error(e);showToast("Error: "+e.message,"error");}
}
async function calcCashFlow(){
  const inn=parseFloat(document.getElementById("cfIn").value||0);
  const out=parseFloat(document.getElementById("cfOut").value||0);
  try{
    const d=await apiPost("/calculate/cashflow",{inflows:[inn],outflows:[out]});
    document.getElementById("cfResult").innerHTML=fmtResultCard("Net Cash Flow","Rs."+d.net_cash_flow);
  }catch(e){console.error(e);showToast("Error: "+e.message,"error");}
}
async function calcEMI(){
  const p=parseFloat(document.getElementById("emiPrincipal").value||0);
  const r=parseFloat(document.getElementById("emiRate").value||0);
  const m=parseInt(document.getElementById("emiMonths").value||0);
  if(!p||!m){showToast("Fill principal and tenure","error");return;}
  try{
    const d=await apiPost("/calculate/emi",{principal:p,annual_rate:r,tenure_months:m});
    document.getElementById("emiResult").innerHTML=fmtResultCard("Monthly EMI","Rs."+d.emi);
  }catch(e){console.error(e);showToast("Error: "+e.message,"error");}
}
async function calcGST(){
  const amt=parseFloat(document.getElementById("gstAmount").value||0);
  const rate=parseFloat(document.getElementById("gstRate").value||0);
  const inclusive=document.getElementById("gstType").value==="true";
  if(!amt||!rate){showToast("Enter amount and rate","error");return;}
  try{
    const d=await apiPost("/calculate/gst",{amount:amt,rate:rate,inclusive});
    document.getElementById("gstResult").innerHTML=fmtResultCard("Total Amount","Rs."+d.total_amount);
  }catch(e){console.error(e);showToast("Error: "+e.message,"error");}
}

/* REMINDERS */
function toggleReminders(){
  const dd=document.getElementById("remindersDropdown");
  dd.classList.toggle("open");
  if(dd.classList.contains("open")) loadRemindersDropdown();
}

async function loadRemindersDropdown(){
  const list=document.getElementById("remindersList");
  try{
    const d=await fetch(API+"/reminders/dashboard").then(r=>r.json());
    const all=[...d.overdue,...d.upcoming];
    const dot=document.getElementById("notifDot");
    if(dot)dot.style.display=all.length?'block':'none';
    if(!all.length){list.innerHTML='<div class="rd-empty">✅ No upcoming due dates</div>';return;}
    const icons={overdue:'🔴',upcoming:'🟡'};
    list.innerHTML=all.map(r=>{
      const diff=r.days_remaining;
      const isOv=diff<0;
      const level=isOv?'critical':(diff<=1?'critical':'warning');
      const label=isOv?`Overdue by ${Math.abs(diff)} day(s)`:diff===0?'Due Today':`Due in ${diff} day(s)`;
      return `<div class="rd-item" onclick="openInvoicePanel('${r._id}');toggleReminders()">
        <div class="rd-icon ${level}">${isOv?'🔴':'🟡'}</div>
        <div class="rd-body">
          <div class="rd-vendor">${r.vendor_name}</div>
          <div class="rd-meta">Due: ${r.due_date} &nbsp;·&nbsp; Rs.${parseFloat(r.total_amount||0).toFixed(2)}</div>
          <span class="rd-tag ${level}">${label}</span>
        </div>
      </div>`;
    }).join('');
  }catch(e){list.innerHTML='<div class="rd-empty">Could not load reminders</div>';}
}

async function loadReminderWidgets(){
  try{
    const d=await fetch(API+"/reminders/dashboard").then(r=>r.json());
    const up=d.upcoming||[];
    const ov=d.overdue||[];
    const due7=up.filter(i=>i.days_remaining<=7).length;
    const due3=up.filter(i=>i.days_remaining<=3).length;
    const due1=up.filter(i=>i.days_remaining<=1).length;
    const el=document.getElementById("reminderWidgets");if(!el)return;
    el.innerHTML=`
      <div class="rem-widget info" onclick="show('invoices',null)">
        <div class="rw-icon">📅</div>
        <div class="rw-body"><div class="rw-num">${due7}</div><div class="rw-label">Due in 7 Days</div></div>
      </div>
      <div class="rem-widget warning" onclick="show('invoices',null)">
        <div class="rw-icon">⚠️</div>
        <div class="rw-body"><div class="rw-num">${due3}</div><div class="rw-label">Due in 3 Days</div></div>
      </div>
      <div class="rem-widget critical" onclick="show('invoices',null)">
        <div class="rw-icon">🔔</div>
        <div class="rw-body"><div class="rw-num">${due1}</div><div class="rw-label">Due Tomorrow</div></div>
      </div>
      <div class="rem-widget overdue" onclick="show('invoices',null)">
        <div class="rw-icon">🔴</div>
        <div class="rw-body"><div class="rw-num">${ov.length}</div><div class="rw-label">Overdue Invoices</div></div>
      </div>
      <div class="rem-widget amount" onclick="show('invoices',null)">
        <div class="rw-icon">💰</div>
        <div class="rw-body"><div class="rw-num">Rs.${(d.total_overdue_amount+d.total_due_this_week).toFixed(0)}</div><div class="rw-label">Total Outstanding</div></div>
      </div>`;
    // update notification dot
    const dot=document.getElementById("notifDot");
    if(dot)dot.style.display=(ov.length||due1)?'block':'none';
  }catch(e){console.error(e);}
}

// close dropdown when clicking outside
document.addEventListener('click',e=>{
  const dd=document.getElementById("remindersDropdown");
  const btn=document.getElementById("bellBtn");
  if(dd&&btn&&!dd.contains(e.target)&&!btn.contains(e.target))dd.classList.remove("open");
});

/* CHAT */
function toggleChat(){document.getElementById("chat").classList.toggle("open");}
async function sendChat(){
  const input=document.getElementById("chatInput");
  const msg=input.value.trim();if(!msg)return;
  const msgs=document.getElementById("chatMsgs");
  msgs.innerHTML+=`<div class="chat-msg user"><div class="avatar">You</div><div class="bubble">${escHtml(msg)}</div>`;
  input.value="";msgs.scrollTop=msgs.scrollHeight;
  try{
    const d=await(await fetch(API+"/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_id:"admin",message:msg})})).json();
    msgs.innerHTML+=`<div class="chat-msg ai"><div class="avatar">AI</div><div class="bubble">${escHtml(d.response)}</div>`;
    msgs.scrollTop=msgs.scrollHeight;
  }catch(e){showToast("Chat error","error");}
}
function escHtml(t){return t.replace(/[&<>"']/g,m=>({'&':'&amp;','<':'<','>':'>','"':'"','\'':'&#39;'}[m]));}
