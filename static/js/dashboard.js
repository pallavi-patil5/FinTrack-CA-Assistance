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
async function load(){
  try{
    const s=await fetch(API+"/summary/admin").then(r=>r.json());
    const sum=document.getElementById("summary");if(!sum)return;
    sum.innerHTML=`
      <div class="stat-card"><div class="stat-icon emerald"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div><div class="stat-info"><h4>Total Income</h4><p>Rs.${parseFloat(s.total_income||0).toFixed(2)}</p></div>
      <div class="stat-card"><div class="stat-icon rose"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg></div><div class="stat-info"><h4>Total Expense</h4><p>Rs.${parseFloat(s.total_expense||0).toFixed(2)}</p></div>
      <div class="stat-card"><div class="stat-icon indigo"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg></div><div class="stat-info"><h4>Net Balance</h4><p>Rs.${parseFloat(s.net_balance||0).toFixed(2)}</p></div>`;
    if(chartInstance)chartInstance.destroy();
    const ctx=document.getElementById("chart");if(!ctx)return;
    chartInstance=new Chart(ctx.getContext("2d"),{type:'bar',data:{labels:["Income","Expense"],datasets:[{data:[s.total_income||0,s.total_expense||0],backgroundColor:['#10b981','#ef4444'],borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:'#e2e8f0'}}}}});
  }catch(e){console.error(e)}
}

/* TRANSACTIONS */
async function loadTransactions(){
  try{
    const tx=await fetch(API+"/transactions/admin").then(r=>r.json());
    const tb=document.getElementById("txnTable");if(!tb)return;
    tb.innerHTML=tx.transactions.map(t=>`<tr><td><span class="badge ${t.type==='Income'?'paid':'rose'}">${t.type}</span></td><td class="amount">Rs.${parseFloat(t.amount||0).toFixed(2)}</td><td>${t.category}</td><td>${t.note||'-'}</td><td>${t.date||'-'}</td></tr>`).join('');
  }catch(e){console.error(e)}
}

function openTxnModal(){document.getElementById("txnModal").classList.add("open");}
function closeTxnModal(){document.getElementById("txnModal").classList.remove("open");}

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
async function uploadInvoice(){
  const file=document.getElementById("fileInput").files[0];
  const invoiceType=document.getElementById("invoiceTypeSelect").value;
  if(!file){showToast("Select a file first","error");return;}
  const fd=new FormData();fd.append("file",file);fd.append("invoice_type",invoiceType);
  try{
    const r=await fetch(API+"/upload-invoice",{method:"POST",body:fd});
    if(!r.ok){const err=await r.json();showToast("Upload failed: "+(err.detail||r.statusText),"error");return;}
    showToast("Invoice processed!");await loadInvoices();load();
  }catch(e){showToast("Error uploading: "+e.message,"error");}
}

async function loadInvoices(){
  try{
    const d=await fetch(API+"/invoices/list/admin").then(r=>r.json());
    const tb=document.getElementById("invTable");if(!tb)return;
    tb.innerHTML=d.invoices.map(i=>{
      const st=(i.status||'pending').toLowerCase();
      const catCls=(i.category||'Expense').toLowerCase();
      const amt=parseFloat(i.total_amount)||0;
      return `<tr onclick="openInvoicePanel('${i._id}')"><td>${i.vendor_name}</td><td class="amount">Rs.${amt.toFixed(2)}</td><td>${i.date||'-'}</td><td>${i.due_date&&i.due_date!=='None'?i.due_date:'-'}</td><td><span class="badge ${st}">${i.status||'Pending'}</span></td><td><span class="badge ${catCls}">${i.category||'Expense'}</span></td></tr>`;
    }).join('');
  }catch(e){console.error(e)}
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
      <h4 style="margin-top:16px;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--text-secondary)">Invoices</h4>
      <table class="vendor-inv-table"><thead><tr><th>Amount</th><th>Status</th><th>Date</th><th>Type</th></tr></thead><tbody>${invRows}</tbody></table>`;
    document.getElementById("vendorPanel").classList.add("open");
  }catch(e){console.error(e)}
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
