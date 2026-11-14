from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

MARKETPLACE = r"""
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AutoFlow — найти автосервис</title>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#172333;background:#f4f7f8}*{box-sizing:border-box}body{margin:0}header{background:#101d2b;color:#fff;padding:18px max(5vw,20px);display:flex;justify-content:space-between;align-items:center}.brand{font-size:24px;font-weight:850;letter-spacing:-1px}.brand span{color:#6ed49d}a{color:inherit;text-decoration:none}.wrap{max-width:1180px;margin:auto;padding:32px 20px}.hero{padding:42px;border-radius:24px;background:linear-gradient(120deg,#12283a,#234e50);color:white}.hero h1{font-size:clamp(30px,5vw,52px);line-height:1.04;max-width:720px;margin:0 0 12px}.hero p{color:#c5d6dc;max-width:600px}.search{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:10px;margin-top:25px}.search input,.search select{padding:14px;border:1px solid #d4dde3;border-radius:10px;background:white;font:inherit;min-width:0}.btn{border:0;border-radius:10px;padding:13px 18px;background:#71d5a0;color:#10251b;font-weight:800;cursor:pointer}.btn.dark{background:#172c3b;color:#fff}.section{margin:34px 0 16px;display:flex;justify-content:space-between;align-items:end;gap:12px}.section h2{margin:0;font-size:25px}.muted{color:#68798a}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{background:white;border:1px solid #e0e7ea;border-radius:16px;padding:20px;box-shadow:0 8px 24px #162d3b0a}.card h3{margin:0 0 6px}.chip{display:inline-block;background:#e8f7ef;color:#20764a;border-radius:20px;padding:5px 9px;font-size:12px;font-weight:700}.price{font-size:22px;font-weight:800;margin:12px 0}.card .btn{width:100%;margin-top:12px}.empty{padding:35px;text-align:center;color:#68798a;background:white;border-radius:16px}.catalog-footer{display:flex;justify-content:center;align-items:center;gap:12px;flex-wrap:wrap;margin:18px 0}.catalog-footer .btn{min-width:190px}.toplink{color:#c9d7df;font-size:14px}@media(max-width:850px){.search{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr 1fr}}@media(max-width:560px){.hero{padding:26px}.search,.grid{grid-template-columns:1fr}.wrap{padding:22px 14px}.section{align-items:start;flex-direction:column}}
.booking-dialog{width:min(620px,calc(100% - 24px));max-height:calc(100% - 24px);overflow:auto;border:1px solid #dce5e8;border-radius:20px;padding:24px;color:#172333;box-shadow:0 24px 80px #07152240}
.booking-dialog::backdrop{background:#071522a8;backdrop-filter:blur(3px)}
.dialog-header{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:20px}
.dialog-header h2{margin:12px 0 5px;font-size:25px}
.dialog-header p{margin:0}
.dialog-close{width:38px;height:38px;flex:0 0 38px;border:0;border-radius:50%;background:#edf2f4;color:#172333;font-size:25px;cursor:pointer}
.booking-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.booking-field{display:flex;flex-direction:column;gap:6px;min-width:0}
.booking-field.full{grid-column:1/-1}
.booking-dialog label,.slot-heading{font-size:13px;font-weight:750;color:#34495a}
.booking-dialog input,.booking-dialog textarea{width:100%;min-width:0;padding:12px;border:1px solid #cbd7dc;border-radius:9px;background:#fff;color:#172333;font:inherit}
.booking-dialog input:focus,.booking-dialog textarea:focus,.slot-button:focus-visible,.btn:focus-visible,.dialog-close:focus-visible{outline:3px solid #299b68;outline-offset:2px}
.booking-dialog textarea{resize:vertical}
.booking-date{margin-top:14px}
.slot-heading{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:18px 0 9px}
.booking-slots{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;min-height:42px}
.slot-button{padding:10px 6px;border:1px solid #cbd7dc;border-radius:9px;background:#f7faf9;color:#172333;font:inherit;font-weight:700;cursor:pointer}
.slot-button[aria-pressed=true]{border-color:#218657;background:#e4f7ed;color:#145b39}
.booking-message{min-height:20px;margin:12px 0 0;color:#526779;font-size:14px}
.booking-message[data-kind=error]{color:#a52c2c}
.booking-message[data-kind=success]{color:#176c43}
.dialog-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:18px}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn.secondary{background:#edf2f4;color:#263b4b}
.booking-success{padding:24px 10px;text-align:center}
.booking-success .success-mark{font-size:36px;color:#218657}
.booking-success h3{margin:8px 0}
[hidden]{display:none!important}
@media(max-width:560px){.booking-dialog{padding:19px}.booking-fields{grid-template-columns:1fr}.booking-field.full{grid-column:auto}.booking-slots{grid-template-columns:repeat(3,minmax(0,1fr))}.dialog-actions{flex-direction:column-reverse}.dialog-actions .btn{width:100%}}
</style></head><body>
<header><a class="brand" href="/marketplace">Auto<span>Flow</span></a><div class="row"><a class="toplink" href="/">Кабинет автосервиса</a></div></header>
<main class="wrap"><section class="hero"><span class="chip">САНКТ-ПЕТЕРБУРГ · ЛЕНИНГРАДСКАЯ ОБЛАСТЬ</span><h1>Найдите автосервис. Запишитесь без звонков.</h1><p>Сравнивайте услуги и цены, выбирайте удобный сервис и отправляйте заявку на запись онлайн.</p>
<form id="search" class="search"><input name="q" placeholder="Услуга или название автосервиса"><select name="city"><option value="">Все города</option><option>Санкт-Петербург</option><option>Всеволожск</option><option>Гатчина</option><option>Выборг</option><option>Кудрово</option><option>Мурино</option></select><select name="category"><option value="">Все услуги</option><option>ТО</option><option>Диагностика</option><option>Ремонт двигателя</option><option>Шиномонтаж</option><option>Тормозная система</option><option>Электрика</option></select><button class="btn">Найти</button></form></section>
<div class="section"><div><h2>Автосервисы и услуги</h2><div class="muted">Выбирайте подходящий вариант и отправляйте заявку</div></div><span id="count" class="muted"></span></div><div id="results" class="grid"><div class="empty">Загружаем каталог…</div></div><div class="catalog-footer"><button id="loadMore" class="btn dark" type="button" hidden>Показать ещё</button><span id="catalogMessage" class="muted" role="status" aria-live="polite"></span></div></main>

<dialog id="bookingDialog" class="booking-dialog" aria-labelledby="bookingTitle">
  <div class="dialog-header">
    <div><span class="chip">ОНЛАЙН-ЗАПИСЬ</span><h2 id="bookingTitle">Запись в автосервис</h2><p id="bookingSubtitle" class="muted"></p></div>
    <button type="button" class="dialog-close" id="closeBooking" aria-label="Закрыть окно записи">×</button>
  </div>
  <form id="bookingForm">
    <div id="bookingDetails">
      <div class="booking-fields">
        <div class="booking-field"><label for="bookingName">Ваше имя</label><input id="bookingName" name="customer_name" required minlength="2" maxlength="160" autocomplete="name"></div>
        <div class="booking-field"><label for="bookingPhone">Телефон для связи</label><input id="bookingPhone" name="customer_phone" type="tel" required minlength="6" maxlength="32" autocomplete="tel" placeholder="+7 900 000-00-00"></div>
        <div class="booking-field full"><label for="bookingEmail">Email (необязательно)</label><input id="bookingEmail" name="customer_email" type="email" maxlength="254" autocomplete="email"></div>
        <div class="booking-field full"><label for="bookingComment">Комментарий (необязательно)</label><textarea id="bookingComment" name="comment" rows="2" maxlength="2000" placeholder="Например, удобное время для звонка или описание проблемы"></textarea></div>
      </div>
      <div class="booking-field booking-date"><label for="bookingDate">Дата записи</label><input id="bookingDate" name="day" type="date" required></div>
      <div class="slot-heading"><span>Свободное время</span><span id="bookingHours" class="muted"></span></div>
      <div id="bookingSlots" class="booking-slots" role="group" aria-label="Доступное время для записи" aria-live="polite">Выберите дату, чтобы увидеть свободное время.</div>
    </div>
    <div id="bookingSuccess" class="booking-success" hidden>
      <div class="success-mark" aria-hidden="true">✓</div><h3>Заявка отправлена</h3><p id="bookingSuccessText" class="muted"></p>
    </div>
    <p id="bookingMessage" class="booking-message" role="status" aria-live="polite"></p>
    <div class="dialog-actions">
      <button type="button" id="cancelBooking" class="btn secondary">Отмена</button>
      <button type="submit" id="submitBooking" class="btn" disabled>Отправить заявку</button>
    </div>
  </form>
</dialog>
<script>
const $=s=>document.querySelector(s);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const PAGE_SIZE=24;
let catalogOffset=0;
let catalogLoading=false;
function serviceCard(x){
 return '<article class="card"><span class="chip">'+esc(x.category)+'</span><h3>'+esc(x.business)+'</h3><div class="muted">'+esc(x.city)+(x.district?' · '+esc(x.district):'')+' · '+esc(x.address)+'</div><h3 style="margin-top:16px">'+esc(x.service)+'</h3><div class="muted">'+esc(x.description||'Услуга автосервиса')+'</div><div class="price">'+(x.price_from_rub===null?'Цена по запросу':'от '+Number(x.price_from_rub).toLocaleString('ru-RU')+' ₽')+'</div><div class="muted">Ориентировочно '+x.duration_minutes+' минут · '+esc(x.phone)+'</div><button class="btn" data-service-id="'+x.service_id+'" data-service="'+esc(x.service)+'" data-business="'+esc(x.business)+'" type="button">Записаться</button></article>';
}
async function load(append=false){
 if(catalogLoading)return;
 catalogLoading=true;
 const button=$('#loadMore');
 const message=$('#catalogMessage');
 const offset=append?catalogOffset:0;
 const params=new URLSearchParams();
 for(const [key,value] of new FormData($('#search'))){
  const normalized=value.trim();
  if(normalized)params.set(key,normalized);
 }
 params.set('limit',String(PAGE_SIZE+1));
 params.set('offset',String(offset));
 button.disabled=true;
 button.hidden=true;
 message.textContent=append?'Загружаем следующие предложения…':'';
 if(!append){
  catalogOffset=0;
  $('#count').textContent='';
  $('#results').innerHTML='<div class="empty">Загружаем каталог…</div>';
 }
 try{
  const response=await fetch('/api/marketplace/services?'+params);
  const data=await response.json().catch(()=>[]);
  if(!response.ok)throw Error(data.detail||'Не удалось загрузить каталог');
  if(!Array.isArray(data))throw Error('Сервер вернул некорректный список предложений');
  const page=data.slice(0,PAGE_SIZE);
  const markup=page.map(serviceCard).join('');
  if(append){
   if(markup)$('#results').insertAdjacentHTML('beforeend',markup);
  }else{
   $('#results').innerHTML=markup||'<div class="empty" style="grid-column:1/-1">Пока нет опубликованных предложений. Попробуйте изменить фильтры или вернитесь позже.</div>';
  }
  catalogOffset+=page.length;
  const hasMore=data.length>PAGE_SIZE;
  button.hidden=!hasMore;
  $('#count').textContent='Загружено: '+catalogOffset;
  message.textContent=hasMore?'Можно загрузить следующие предложения.':(catalogOffset?'Все предложения загружены.':'Пока нет опубликованных предложений.');
 }catch(error){
  if(!append)$('#results').innerHTML='<div class="empty">Не удалось загрузить каталог. Обновите страницу.</div>';
  message.textContent=error.message||'Не удалось загрузить каталог.';
  button.hidden=catalogOffset===0;
 }finally{
  catalogLoading=false;
  button.disabled=false;
 }
}
$('#loadMore').addEventListener('click',()=>load(true));
const bookingDialog=$('#bookingDialog');
const bookingForm=$('#bookingForm');
const bookingDate=$('#bookingDate');
const bookingSlots=$('#bookingSlots');
const bookingMessage=$('#bookingMessage');
const bookingHours=$('#bookingHours');
const submitBooking=$('#submitBooking');
const bookingDetails=$('#bookingDetails');
const bookingSuccess=$('#bookingSuccess');
const cancelBooking=$('#cancelBooking');
let activeServiceId=null;
let selectedStartAt=null;
let availabilityRequest=0;
function moscowDateValue(){return new Date(Date.now()+180*60*1000).toISOString().slice(0,10)}
function setBookingMessage(message,kind='info'){bookingMessage.textContent=message;bookingMessage.dataset.kind=kind}
function formatBookingTime(value){return new Date(value).toLocaleTimeString('ru-RU',{timeZone:'Europe/Moscow',hour:'2-digit',minute:'2-digit'})}
async function loadBookingSlots(){
 const requestId=++availabilityRequest;
 selectedStartAt=null;
 submitBooking.disabled=true;
 bookingHours.textContent='';
 bookingSlots.replaceChildren();
 const day=bookingDate.value;
 if(!day){bookingSlots.textContent='Выберите дату, чтобы увидеть свободное время.';return}
 bookingSlots.textContent='Проверяем свободное время…';
 try{
  const query=new URLSearchParams({service_id:String(activeServiceId),day,utc_offset_minutes:'180'});
  const response=await fetch('/api/marketplace/availability?'+query);
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw Error(data.detail||'Не удалось проверить свободное время');
  if(requestId!==availabilityRequest)return;
  const hours=data.working_hours||{};
  bookingHours.textContent=hours.is_closed?'Выходной':(hours.from&&hours.to?'Рабочее время '+hours.from+'–'+hours.to:'');
  if(!Array.isArray(data.slots)||!data.slots.length){
   bookingSlots.textContent=hours.is_closed?'В этот день автосервис не работает.':'На эту дату свободного времени нет. Выберите другой день.';
   return;
  }
  bookingSlots.replaceChildren();
  for(const slot of data.slots){
   const option=document.createElement('button');
   option.type='button';
   option.className='slot-button';
   option.textContent=formatBookingTime(slot);
   option.setAttribute('aria-pressed','false');
   option.addEventListener('click',()=>{
    selectedStartAt=slot;
    bookingSlots.querySelectorAll('.slot-button').forEach(item=>item.setAttribute('aria-pressed',String(item===option)));
    submitBooking.disabled=false;
    setBookingMessage('Выбрано время '+formatBookingTime(slot)+'.','info');
   });
   bookingSlots.append(option);
  }
 }catch(error){
  if(requestId!==availabilityRequest)return;
  bookingSlots.textContent='Не удалось загрузить свободное время.';
  setBookingMessage(error.message,'error');
 }
}
function openBooking(button){
 activeServiceId=Number(button.dataset.serviceId);
 if(!Number.isSafeInteger(activeServiceId)||activeServiceId<1)return;
 bookingForm.reset();
 bookingDetails.hidden=false;
 bookingSuccess.hidden=true;
 submitBooking.hidden=false;
 submitBooking.textContent='Отправить заявку';
 cancelBooking.textContent='Отмена';
 selectedStartAt=null;
 bookingDate.min=moscowDateValue();
 bookingDate.value=bookingDate.min;
 $('#bookingTitle').textContent='Запись на услугу «'+button.dataset.service+'»';
 $('#bookingSubtitle').textContent=button.dataset.business;
 bookingHours.textContent='';
 bookingSlots.textContent='Проверяем свободное время…';
 setBookingMessage('');
 submitBooking.disabled=true;
 bookingDialog.showModal();
 $('#bookingName').focus();
 loadBookingSlots();
}
$('#results').addEventListener('click',event=>{
 const button=event.target.closest('[data-service-id]');
 if(button)openBooking(button);
});
bookingDate.addEventListener('change',()=>{setBookingMessage('');loadBookingSlots()});
$('#closeBooking').addEventListener('click',()=>bookingDialog.close());
cancelBooking.addEventListener('click',()=>bookingDialog.close());
bookingDialog.addEventListener('click',event=>{if(event.target===bookingDialog)bookingDialog.close()});
bookingDialog.addEventListener('close',()=>{
 availabilityRequest++;
 bookingForm.reset();
 bookingDetails.hidden=false;
 bookingSuccess.hidden=true;
 submitBooking.hidden=false;
 submitBooking.textContent='Отправить заявку';
 cancelBooking.textContent='Отмена';
 selectedStartAt=null;
 activeServiceId=null;
 setBookingMessage('');
});
bookingForm.addEventListener('submit',async event=>{
 event.preventDefault();
 if(!bookingForm.reportValidity())return;
 if(!selectedStartAt){setBookingMessage('Сначала выберите свободное время.','error');return}
 const payload={
  service_id:activeServiceId,
  customer_name:bookingForm.elements.customer_name.value.trim(),
  customer_phone:bookingForm.elements.customer_phone.value.trim(),
  starts_at:selectedStartAt
 };
 const email=bookingForm.elements.customer_email.value.trim();
 const comment=bookingForm.elements.comment.value.trim();
 if(email)payload.customer_email=email;
 if(comment)payload.comment=comment;
 submitBooking.disabled=true;
 setBookingMessage('Отправляем заявку…');
 try{
  const response=await fetch('/api/marketplace/bookings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const data=await response.json().catch(()=>({}));
  if(!response.ok){
   if(response.status===409){
    setBookingMessage('Это время только что заняли. Обновляем список свободных интервалов…','error');
    await loadBookingSlots();
    setBookingMessage('Выберите другое доступное время и отправьте заявку ещё раз.','error');
    return;
   }
   throw Error(data.detail||'Не удалось отправить заявку');
  }
  bookingDetails.hidden=true;
  bookingSuccess.hidden=false;
  $('#bookingSuccessText').textContent='Заявка №'+data.id+' отправлена в '+$('#bookingSubtitle').textContent+'. Автосервис должен подтвердить время.';
  bookingSlots.replaceChildren();
  bookingHours.textContent='';
  bookingMessage.textContent='';
  submitBooking.hidden=true;
  cancelBooking.textContent='Готово';
 }catch(error){
  setBookingMessage(error.message,'error');
  submitBooking.disabled=!selectedStartAt;
 }
});
$('#search').addEventListener('submit',e=>{e.preventDefault();load(false)});load(false);
</script></body></html>
"""

@router.get("/marketplace", response_class=HTMLResponse, include_in_schema=False)
def marketplace_home():
    return MARKETPLACE

PARTNER = r"""
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AutoFlow — кабинет партнёра</title>
<style>body{margin:0;background:#0b1421;color:#eaf0f7;font:15px Inter,Segoe UI,Arial}header{padding:18px 5%;background:#111f30;display:flex;justify-content:space-between}.brand{font-size:23px;font-weight:800}.brand span{color:#71d5a0}main{max-width:1100px;margin:28px auto;padding:0 18px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel{background:#142338;border:1px solid #2b4058;border-radius:16px;padding:20px}input,textarea,select{box-sizing:border-box;width:100%;padding:11px;margin:6px 0 12px;border-radius:8px;border:1px solid #40546b;background:#0b1829;color:#fff}label{font-size:13px;color:#a9bbce}.btn{background:#71d5a0;color:#092018;border:0;padding:11px 16px;border-radius:9px;font-weight:800;cursor:pointer}.item{padding:12px 0;border-bottom:1px solid #2b4058}.muted{color:#9db0c4}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.hours-row{display:grid;grid-template-columns:1.2fr auto 1fr 1fr;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid #2b4058}.hours-row input[type=checkbox]{width:auto;margin:0}.hours-row input[type=time]{margin:0}@media(max-width:700px){.grid{grid-template-columns:1fr}.hours-row{grid-template-columns:1fr 1fr}.hours-row strong{grid-column:1/-1}}</style></head><body><header><div class="brand">Auto<span>Flow</span> / Партнёр</div><a href="/marketplace" style="color:#b8c9d8">Каталог</a></header><main><h1>Кабинет автосервиса</h1><p class="muted">Заполните профиль и добавьте услуги. После проверки профиль появится в каталоге.</p><div class="grid"><section class="panel"><h2>Публичный профиль</h2><form id="profile"><label>Название автосервиса</label><input name="public_name" required><label>Город</label><input name="city" value="Санкт-Петербург" required><label>Район</label><input name="district"><label>Адрес</label><input name="address" required><label>Телефон</label><input name="phone" required><label>Описание</label><textarea name="description"></textarea><label>Сайт</label><input name="website"><button class="btn">Сохранить профиль</button></form><p id="profilemsg" class="muted"></p></section><section class="panel"><h2>Добавить услугу</h2><form id="service"><label>Название услуги</label><input name="title" required><label>Категория</label><select name="category"><option>ТО</option><option>Диагностика</option><option>Ремонт двигателя</option><option>Шиномонтаж</option><option>Тормозная система</option><option>Электрика</option><option>Кузовной ремонт</option><option>Другое</option></select><label>Цена от, ₽</label><input name="price_from_rub" type="number" min="0"><label>Длительность, минут</label><input name="duration_minutes" type="number" min="15" max="1440" value="60"><label>Описание</label><textarea name="description"></textarea><button class="btn">Добавить услугу</button></form><div id="services"></div></section><section class="panel" style="grid-column:1/-1"><h2>График работы</h2><p class="muted">Укажите часы работы по дням недели. Новые заявки будут доступны только в эти интервалы. По умолчанию действует график 09:00–18:00.</p><div id="hours"></div><button type="button" class="btn" id="savehours">Сохранить график</button><p id="hoursmsg" class="muted"></p></section><section class="panel" style="grid-column:1/-1"><h2>Заявки на запись</h2><div id="bookings" class="muted">Загрузка…</div></section></div></main>
<script>const $=s=>document.querySelector(s);async function api(url,opt={}){let r=await fetch(url,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});let d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||'Ошибка запроса');return d}const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const weekdayNames=['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье'];function renderHours(days){$('#hours').innerHTML=days.map(day=>'<div class="hours-row"><strong>'+weekdayNames[day.weekday]+'</strong><label><input type="checkbox" data-open '+(!day.is_closed?'checked':'')+'> Работает</label><input type="time" aria-label="Открытие — '+weekdayNames[day.weekday]+'" step="1800" data-from value="'+(day.opens_at||'09:00')+'" '+(day.is_closed?'disabled':'')+'><input type="time" aria-label="Закрытие — '+weekdayNames[day.weekday]+'" step="1800" data-to value="'+(day.closes_at||'18:00')+'" '+(day.is_closed?'disabled':'')+'></div>').join('');$('#hours').querySelectorAll('.hours-row').forEach(row=>{const open=row.querySelector('[data-open]');const from=row.querySelector('[data-from]');const to=row.querySelector('[data-to]');open.addEventListener('change',()=>{from.disabled=!open.checked;to.disabled=!open.checked})})}async function load(){try{let p=await api('/api/partner/profile');if(p)for(let [k,v] of Object.entries({public_name:p.name,city:p.city,district:p.district,address:p.address,phone:p.phone,description:p.description,website:p.website}))$('#profile').elements[k].value=v||'';let hours=await api('/api/partner/working-hours');renderHours(hours.days);let services=await api('/api/partner/services');$('#services').innerHTML=services.map(s=>'<div class="item"><b>'+esc(s.title)+'</b><div class="muted">'+esc(s.category)+' · '+(s.price_from_rub??'цена по запросу')+' ₽ · '+s.duration_minutes+' мин</div></div>').join('');let bookings=await api('/api/partner/bookings');$('#bookings').innerHTML=bookings.length?bookings.map(b=>'<div class="item"><b>'+esc(b.customer_name)+' · '+esc(b.service)+'</b><div class="muted">'+esc(b.customer_phone)+' · '+new Date(b.starts_at).toLocaleString('ru-RU')+' · '+esc(b.status)+'</div><div class="row">'+(b.status==='pending'?'<button class="btn" onclick="status('+b.id+',\'confirmed\')">Подтвердить</button>':'')+(b.status==='pending'||b.status==='confirmed'?'<button class="btn" onclick="status('+b.id+',\'cancelled\')">Отменить</button>':'')+'</div></div>').join(''):'Пока заявок нет.'}catch(e){$('#bookings').textContent=e.message+' — сначала войдите в аккаунт на главной странице.'}}async function status(id,s){try{await api('/api/partner/bookings/'+id,{method:'PATCH',body:JSON.stringify({status:s})});load()}catch(e){alert(e.message)}}$('#savehours').onclick=async()=>{const days=Array.from($('#hours').querySelectorAll('.hours-row')).map((row,weekday)=>({weekday,is_closed:!row.querySelector('[data-open]').checked,opens_at:row.querySelector('[data-from]').value||null,closes_at:row.querySelector('[data-to]').value||null}));try{const result=await api('/api/partner/working-hours',{method:'PUT',body:JSON.stringify({days})});renderHours(result.days);$('#hoursmsg').textContent='График сохранён. Новые заявки будут учитывать его.'}catch(e){$('#hoursmsg').textContent=e.message}};$('#profile').onsubmit=async e=>{e.preventDefault();let d=Object.fromEntries(new FormData(e.target));try{let p=await api('/api/partner/profile',{method:'PUT',body:JSON.stringify(d)});$('#profilemsg').textContent=p.is_published?'Профиль сохранён и опубликован':'Профиль сохранён. Ожидает проверки администратора.'}catch(e){$('#profilemsg').textContent=e.message}};$('#service').onsubmit=async e=>{e.preventDefault();let d=Object.fromEntries(new FormData(e.target));d.price_from_rub=d.price_from_rub?Number(d.price_from_rub):null;d.duration_minutes=Number(d.duration_minutes);try{await api('/api/partner/services',{method:'POST',body:JSON.stringify(d)});e.target.reset();load()}catch(e){alert(e.message)}};load();</script></body></html>
"""

PLATFORM = r"""
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AutoFlow — управление платформой</title>
<style>body{margin:0;background:#0b1421;color:#eaf0f7;font:15px Inter,Segoe UI,Arial}header{padding:18px 5%;background:#111f30}.brand{font-size:23px;font-weight:800}.brand span{color:#71d5a0}main{max-width:1200px;margin:28px auto;padding:0 18px}.stats,.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat,.panel{background:#142338;border:1px solid #2b4058;border-radius:15px;padding:18px}.stat b{display:block;font-size:28px;margin-top:8px}.grid{grid-template-columns:1fr 1fr;margin-top:16px}.item{padding:13px 0;border-bottom:1px solid #2b4058}.muted{color:#9db0c4}.btn{background:#71d5a0;color:#092018;border:0;padding:8px 12px;border-radius:8px;font-weight:800;cursor:pointer}@media(max-width:750px){.stats,.grid{grid-template-columns:1fr 1fr}}@media(max-width:500px){.stats,.grid{grid-template-columns:1fr}}</style></head><body><header><div class="brand">Auto<span>Flow</span> / Администрирование</div></header><main><h1>Панель платформы</h1><div id="stats" class="stats"></div><div class="grid"><section class="panel"><h2>Автосервисы</h2><div id="businesses">Загрузка…</div></section><section class="panel"><h2>Заявки и клиенты</h2><div id="bookings">Загрузка…</div></section></div></main><script>const $=s=>document.querySelector(s);async function api(url,opt={}){let r=await fetch(url,{...opt,headers:{'Content-Type':'application/json',...(opt.headers||{})}});let d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||'Нет доступа или ошибка запроса');return d}const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function load(){try{let [o,b,book,clients]=await Promise.all([api('/api/platform/overview'),api('/api/platform/businesses'),api('/api/platform/bookings'),api('/api/platform/clients')]);$('#stats').innerHTML=[['Организации',o.organizations],['Опубликовано',o.published_businesses],['Клиенты',o.customers],['Заявки',o.booking_requests],['Ожидают подтверждения',o.pending_bookings]].map(x=>'<div class="stat"><span class="muted">'+x[0]+'</span><b>'+x[1]+'</b></div>').join('');$('#businesses').innerHTML=b.length?b.map(x=>'<div class="item"><b>'+esc(x.name)+'</b><div class="muted">'+esc(x.city)+' · '+esc(x.address)+' · услуг: '+x.services_count+'</div><div class="muted">'+x.services.map(s=>esc(s.title)).join(', ')+'</div><button class="btn" onclick="publish('+x.organization_id+')">'+(x.is_published?'Снять с публикации':'Опубликовать')+'</button></div>').join(''):'Пока нет профилей';$('#bookings').innerHTML='<h3>Заявки</h3>'+(book.length?book.map(x=>'<div class="item"><b>'+esc(x.customer_name)+' · '+esc(x.business)+'</b><div class="muted">'+esc(x.customer_phone)+' · '+esc(x.service)+' · '+new Date(x.starts_at).toLocaleString('ru-RU')+' · '+esc(x.status)+'</div></div>').join(''):'Заявок пока нет')+'<h3>Клиенты автосервисов</h3>'+(clients.length?clients.map(x=>'<div class="item"><b>'+esc(x.name)+'</b><div class="muted">'+esc(x.organization)+' · '+esc(x.phone||x.email||'Контакты не указаны')+'</div></div>').join(''):'Клиентов пока нет')}catch(e){$('#stats').textContent=e.message+'; настройте PLATFORM_ADMIN_EMAIL и войдите администратором.'}}async function publish(id){try{await api('/api/platform/businesses/'+id+'/publish',{method:'PATCH'});load()}catch(e){alert(e.message)}}load();</script></body></html>
"""

@router.get("/partner", response_class=HTMLResponse, include_in_schema=False)
def partner_home():
    return PARTNER

@router.get("/platform", response_class=HTMLResponse, include_in_schema=False)
def platform_home():
    return PLATFORM
