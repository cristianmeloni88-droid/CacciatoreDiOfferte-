let prodotti=JSON.parse(localStorage.getItem('shardan_prodotti')||'null')||[];
async function load(){ if(!prodotti.length){ const r=await fetch('prodotti.json'); prodotti=await r.json(); salva(); } render(); }
function salva(){ localStorage.setItem('shardan_prodotti',JSON.stringify(prodotti)); }
function render(){
 let guadagni=0,click=0,vendite=0; let perShop={};
 prodotti.forEach(p=>{ const g=(p.vendite||0)*(p.prezzo||0)*(p.commissione||5)/100; guadagni+=g; click+=p.click||0; vendite+=p.vendite||0; perShop[p.shop]=(perShop[p.shop]||0)+(p.vendite||0); });
 document.getElementById('guadagni').textContent=guadagni.toFixed(2)+' EUR';
 document.getElementById('click').textContent=click; document.getElementById('vendite').textContent=vendite;
 document.getElementById('conv').textContent=click?((vendite/click*100).toFixed(1)+'%'):'0%';
 document.getElementById('nProdotti').textContent=prodotti.length;
 document.getElementById('shopBars').innerHTML=Object.entries(perShop).map(([s,v])=>`<div>${s} <b>${v}</b> <div style="background:#00d4ff;height:10px;width:${v*20}px"></div></div>`).join('');
 document.getElementById('agenti').innerHTML=AGENTI.map(a=>`<div>● <b>${a.id}</b> ${a.shop} - ${a.compito}</div>`).join('');
 document.getElementById('prodotti').innerHTML=prodotti.map((p,i)=>`<div><b>${p.nome}</b> ${p.prezzo}€ (vecchio ${p.vecchio}€) ${p.shop} - Click ${p.click||0} Vendite ${p.vendite||0} <button onclick="clickProd(${i})">+1 Click</button><button onclick="venditaProd(${i})">+1 Vendita</button><button onclick="eliminaProd(${i})">Elimina</button></div>`).join('');
 document.getElementById('selProdotto').innerHTML=prodotti.map((p,i)=>`<option value="${i}">${p.nome}</option>`).join('');
 let errori=prodotti.filter(p=>p.vecchio && ((p.vecchio-p.prezzo)/p.vecchio*100>70));
 document.getElementById('errori').innerHTML=errori.length?errori.map(p=>`<div style="color:#ff5555">⚠️ ${p.nome} da ${p.vecchio}€ a ${p.prezzo}€ -${(((p.vecchio-p.prezzo)/p.vecchio*100)).toFixed(0)}% - ${p.shop}</div>`).join(''):'✅ Nessun errore rilevato';
}
function clickProd(i){prodotti[i].click=(prodotti[i].click||0)+1;salva();render();parla('Click aggiunto a '+prodotti[i].nome)}
function venditaProd(i){prodotti[i].vendite=(prodotti[i].vendite||0)+1;salva();render();parla('Vendita registrata per '+prodotti[i].nome)}
function eliminaProd(i){prodotti.splice(i,1);salva();render();}
function aggiungiProdotto(){ const p={nome:document.getElementById('fNome').value,prezzo:+document.getElementById('fPrezzo').value,vecchio:+document.getElementById('fVecchio').value,shop:document.getElementById('fShop').value,commissione:+document.getElementById('fComm').value||5,link:document.getElementById('fLink').value,click:0,vendite:0}; if(!p.nome) return alert('Metti nome'); prodotti.push(p); salva(); render(); parla('Prodotto aggiunto '+p.nome); }
function aggiungiUtente(){ let u=+document.getElementById('utenti').textContent+1; document.getElementById('utenti').textContent=u; }
function generaPost(){ const p=prodotti[document.getElementById('selProdotto').value]; if(!p) return; const sconto=p.vecchio?Math.round((p.vecchio-p.prezzo)/p.vecchio*100):0; document.getElementById('postOut').innerHTML=`<p><b>Bot:</b> 🔥 ${p.nome} a ${p.prezzo}€ invece di ${p.vecchio}€ -${sconto}% ${p.link} Come affiliato guadagno dagli acquisti idonei. #ad</p><p><b>Canale:</b> Offerta ${p.shop}: ${p.nome} conviene perché costa ${p.prezzo}€ invece di ${p.vecchio}€. ${p.link} #ad</p><p><b>TikTok:</b> Hook 2 sec: Guarda questo prezzo! ${p.nome} a ${p.prezzo}€...`; parla('Post generati per '+p.nome); }
function riepilogoCapo(){ const g=document.getElementById('guadagni').textContent; document.getElementById('capoOut').innerHTML=`Riepilogo CAPO: Guadagni oggi ${g}, Prodotti attivi ${prodotti.length}, Agenti attivi 10 inclusi TEM e ALI. Pubblico le top 3?`; parla('Riepilogo pronto, guadagni oggi '+g); }
function parla(testo){ document.getElementById('jarvisDice').textContent='JARVIS: '+testo; try{speechSynthesis.cancel(); let u=new SpeechSynthesisUtterance(testo); u.lang='it-IT'; speechSynthesis.speak(u);}catch(e){} }
function attivaVoce(){ parla('Ciao, sono Jarvis, ti sento. Dimmi pure.'); startAscolto(); }
let rec=null;
function startAscolto(){ const SR=window.SpeechRecognition||window.webkitSpeechRecognition; if(!SR){ document.getElementById('trascrizione').textContent='Apri in Chrome/Safari per la voce'; return; } rec=new SR(); rec.lang='it-IT'; rec.continuous=true; rec.interimResults=false; rec.onresult=e=>{ const t=e.results[e.results.length-1][0].transcript.toLowerCase(); document.getElementById('trascrizione').textContent='Hai detto: '+t; gestisciComando(t); }; rec.onend=()=>{ try{rec.start()}catch(e){} }; try{rec.start(); document.getElementById('ascolto').textContent='IN ASCOLTO...';}catch(e){} }
function gestisciComando(t){ if(t.includes('guadagn')) parla('Oggi hai guadagnato '+document.getElementById('guadagni').textContent); else if(t.includes('error')){ const e=document.getElementById('errori').innerText; parla(e); } else if(t.includes('temu')) parla('Temu: agente TEM attivo, controlla offerte Temu'); else if(t.includes('aliexpress')||t.includes('ali')) parla('AliExpress: agente ALI attivo'); else if(t.includes('capo')) riepilogoCapo(); else if(t.includes('post')) generaPost(); else parla('Ricevuto: '+t); }
setInterval(()=>{ document.getElementById('clock').textContent='UTC '+new Date().toISOString().slice(11,19); },1000);
load();
