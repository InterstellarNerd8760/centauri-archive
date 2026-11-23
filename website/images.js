/* The atlas is an editorial plan; planned subjects are not archive files. */
"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const buttons=$("atlas-filters"), output=$("atlas-results"), more=$("atlas-more"), search=$("image-search");
  let index=null,category="all",limit=24;
  function el(tag,text,name){
    const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=text;
    if(name)n.className=name;return n;
  }
  function paintFilters(){
    buttons.replaceChildren();
    const defs=[{id:"all",name:"All categories",target:100},...index.categories];
    defs.forEach(c=>{
      const button=el("button",c.name+" · "+c.target,"atlas-filter");
      button.type="button";button.setAttribute("aria-pressed",String(category===c.id));
      button.addEventListener("click",()=>{category=c.id;limit=24;paint();});
      buttons.append(button);
    });
  }
  function paint(){
    if(!index)return;
    paintFilters();
    const current=index.categories.find(c=>c.id===category);
    $("atlas-category-title").textContent=current?current.name:"The full image plan";
    $("atlas-category-description").textContent=current?current.description:"One hundred deliberate subjects grouped into ten teaching sequences. Browse a section or search across the whole collection.";
    $("atlas-subtitle").textContent=current?"COLLECTION / "+current.id.toUpperCase():"ALL SUBJECTS / 001–100";
    const q=search.value.trim().toLocaleLowerCase();
    const matches=index.records.filter(r=>(category==="all"||r.category===category)&&
      [r.id,r.title,r.kind,r.category].join(" ").toLocaleLowerCase().includes(q));
    $("atlas-count").textContent=matches.length+" image "+(matches.length===1?"subject":"subjects");
    output.replaceChildren();
    const shown=matches.slice(0,limit);
    if(!shown.length)output.append(el("p","No matching subjects. Try a different category or search term.","reader-loading"));
    shown.forEach(record=>{
      const item=el("article",null,"atlas-image-item");
      const media=el("div",null,"atlas-item-media");
      if(record.status==="included"&&record.asset&&/^[a-z0-9/_-]+\.(?:jpe?g|png|webp)$/.test(record.asset)){
        const photo=el("img");photo.src="records/"+record.asset;photo.alt=record.title;
        photo.loading="lazy";media.append(photo);
      }else{
        const marker=el("div",record.id,"atlas-item-placeholder");
        marker.setAttribute("aria-label","No image acquired yet");media.append(marker);
      }
      item.append(media);
      const body=el("div",null,"atlas-item-body");
      body.append(el("span",record.id,"atlas-item-id"));
      const state=el("span",record.status==="included"?"IN ARCHIVE":"PLANNED","atlas-item-status"+(record.status==="included"?" archived":""));
      body.append(state);
      body.append(el("h4",record.title));
      body.append(el("p",record.kind+" · "+record.curation_note));
      if(record.status==="included"&&record.asset){
        const a=el("a","View verified record ↗","text-link");
        a.href="library.html?record="+encodeURIComponent(record.asset);body.append(a);
      }
      item.append(body);output.append(item);
    });
    more.hidden=matches.length<=limit;
    more.textContent="Show "+Math.min(24,matches.length-limit)+" more of "+matches.length;
  }
  search.addEventListener("input",()=>{limit=24;paint();});
  more.addEventListener("click",()=>{limit+=24;paint();});
  fetch("image-plan.json").then(r=>{if(!r.ok)throw Error("Plan missing");return r.json();}).then(data=>{
    if(!Array.isArray(data.categories)||!Array.isArray(data.records)||data.records.length!==100)throw Error("Invalid plan");
    index=data;
    const live=data.records.filter(r=>r.status==="included").length;
    $("atlas-target").textContent=data.records.length;
    $("atlas-included").textContent=live;
    $("atlas-remaining").textContent=data.records.length-live;
    paint();
  }).catch(()=>{
    buttons.textContent="Image categories unavailable.";
    output.textContent="The image plan could not be loaded. The current archive remains accessible from the library.";
  });
})();
