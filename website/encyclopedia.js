"use strict";
const get = id => document.getElementById(id);
const node = (tag, text, cls) => {const e=document.createElement(tag); if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;};
const search=get("enc-search"), categories=get("enc-categories"), body=get("enc-body");
let data, photos=new Map(), records=new Map(), articleMap=new Map(), current=null;
function articleLink(article, cls) {
  const a=node("a",article.title,cls);a.href="?article="+encodeURIComponent(article.id);
  a.dataset.article=article.id;if(current===article.id)a.setAttribute("aria-current","page");
  a.addEventListener("click",event=>{if(event.button||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();select(article.id,true);});return a;
}
function showCategories(){
  const query=search.value.trim().toLowerCase();categories.replaceChildren();let count=0;
  for(const category of data.categories){
    const list=data.articles.filter(a=>a.category===category.id&&[a.id,a.title,a.subcategory,category.title,category.description,...a.body,a.limitations].join(" ").toLowerCase().includes(query));
    if(!list.length)continue;count+=list.length;
    const detail=node("details",null,"enc-category");detail.open=Boolean(query)||list.some(a=>a.id===current);
    const summary=node("summary"), symbol=node("span",category.symbol,"enc-symbol");symbol.setAttribute("aria-hidden","true");
    const copy=node("span");copy.append(node("span",category.id+" — "+category.title,"enc-category-name"),node("span",category.description,"enc-category-description"));
    summary.append(symbol,copy);detail.append(summary);
    for(const a of list)detail.append(articleLink(a,"enc-article-link"));
    categories.append(detail);
  }
  get("enc-count").textContent=count+" / "+data.articles.length+" articles";
  if(!count)categories.append(node("p","No matching articles."));
}
function listLinks(title,items){if(!items.length)return;body.append(node("h3",title));const ul=node("ul");for(const item of items){const li=node("li");li.append(item);ul.append(li);}body.append(ul);}
function renderParagraphs(article) {
  article.body.forEach((text, index) => {
    const paragraph = node("p", text);
    article.sources.forEach((source, sourceIndex) => {
      if (!source.paragraphs?.includes(index + 1)) return;
      const link = node("a", "[" + (sourceIndex + 1) + "]");
      link.href = "#enc-source-" + (sourceIndex + 1);
      link.setAttribute("aria-label", "Source " + (sourceIndex + 1));
      const reference = node("sup");
      reference.append(" ", link);
      paragraph.append(reference);
    });
    body.append(paragraph);
  });
}
function renderTerms(terms) {
  if (!terms?.length) return;
  const list = node("dl", null, "enc-terms");
  for (const {term, definition} of terms) list.append(node("dt", term), node("dd", definition));
  body.append(node("h3", "Key terms"), list);
}
function renderReferences(article) {
  body.append(node("h3", "References and review"));
  if (article.review_stage === "ai-drafted") {
    body.append(node("p", article.sources.length
      ? "These source leads await a claim-by-claim check."
      : "Source verification is pending. Supplementary archive records provide context."));
  }
  if (article.sources.length) {
    const list = node("ol");
    article.sources.forEach((source, index) => {
      const item = node("li");
      item.id = "enc-source-" + (index + 1);
      const link = node("a", source.label);
      try {
        const url = new URL(source.url);
        if (url.protocol === "https:") link.href = url.href;
      } catch {}
      item.append(link);
      if (source.accessed) item.append(" · Accessed " + source.accessed);
      list.append(item);
    });
    body.append(list);
  }
  body.append(node("p", article.credit + " · " + article.rights, "enc-meta"));
  const history = node("details", null, "enc-history");
  const revisions = node("ul");
  for (const revision of article.revision_history ?? []) {
    const date = revision.date ? " · " + revision.date : "";
    revisions.append(node("li", "Revision " + revision.revision + date + " · " + revision.change));
  }
  history.append(node("summary", "Revision history"), revisions);
  body.append(history);
}
function renderDiagrams(paths) {
  const diagrams = paths.filter(path => path.endsWith(".svg"));
  if (!diagrams.length) return;
  body.append(node("h3", "Explanatory diagrams"));
  for (const path of diagrams) {
    const record = records.get(path);
    const link = node("a", null, "enc-diagram");
    link.href = "records/" + path;
    const image = node("img");
    image.src = link.href;
    image.alt = record?.alt ?? record?.title ?? path;
    image.loading = "lazy";
    link.append(image);
    const figure = node("figure");
    figure.append(link, node("figcaption", record?.caption ?? record?.summary ?? ""));
    body.append(figure);
  }
}
function select(id,push=false){
  const a=articleMap.get(id);if(!a)return;current=id;
  get("enc-id").textContent=a.id+" / "+data.categories.find(c=>c.id===a.category).title;
  get("enc-title").textContent=a.title;body.replaceChildren();
  body.append(node("p",a.subcategory+" · Revision "+a.revision+" · "+a.status,"enc-meta"));
  renderParagraphs(a);
  renderTerms(a.terms);
  body.append(node("h3","Interpretation and limitations"),node("p",a.limitations));
  listLinks("Prerequisite concepts",a.prerequisites.map(id=>articleLink(articleMap.get(id))));
  listLinks("Continue learning",data.articles.filter(b=>b.prerequisites.includes(id)).map(b=>articleLink(b)));
  const related=a.images.map(id=>photos.get(id)).filter(p=>p&&p.asset);
  if(related.length){body.append(node("h3","Related photographic records"));const grid=node("div",null,"enc-images");for(const p of related){const link=node("a",null,"enc-image");link.href="images.html?record="+encodeURIComponent(p.asset);const img=node("img");img.src="records/"+p.asset;img.alt=p.title;img.loading="lazy";img.decoding="async";link.append(img,node("span",p.id+" · "+p.title));grid.append(link);}body.append(grid);}
  renderDiagrams(a.records);
  listLinks("Supplementary archive records",a.records.filter(path=>!path.endsWith(".svg")).map(path=>{const link=node("a",records.get(path)?.title ?? path);link.href="records/"+path;return link;}));
  renderReferences(a);
  showCategories();
  if(push){const url=new URL(location.href);url.searchParams.set("article",id);url.hash="";history.pushState({}, "", url);get("enc-title").focus({preventScroll:true});get("enc-reader").scrollIntoView({block:"start"});}
}
async function init(){
  try{
    const responses=await Promise.all([fetch("records/encyclopedia/index.json"),fetch("image-plan.json"),fetch("records/catalog.json")]);
    if(responses.some(r=>!r.ok))throw Error("Index unavailable");
    data=await responses[0].json();const plan=await responses[1].json();const catalog=await responses[2].json();
    photos=new Map(plan.records.map(p=>[p.id,p]));articleMap=new Map(data.articles.map(a=>[a.id,a]));
    records=new Map(catalog.records.map(record=>[record.path,record]));
    const requested=new URL(location.href).searchParams.get("article");select(articleMap.has(requested)?requested:data.articles[0].id);
    search.addEventListener("input",showCategories);
    addEventListener("popstate",()=>{
      const id=new URL(location.href).searchParams.get("article");
      const selected=articleMap.has(id)?id:data.articles[0].id;
      if(selected!==current)select(selected);
    });
  }catch(e){get("enc-count").textContent="Unavailable";categories.textContent="Unable to load the encyclopedia.";body.textContent="The source dataset is available in the downloadable archive.";}
}
init();
