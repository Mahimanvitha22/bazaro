import { useEffect, useState, createContext, useContext, useCallback } from "react";
import { Routes, Route, Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import api, { errText } from "./api";
const Ctx = createContext();
const useApp = () => useContext(Ctx);
const FALLBACK = "/placeholder.svg";
const Img = ({ src, alt = "" }) => <img src={src || FALLBACK} alt={alt} loading="lazy" onError={e => { if (!e.currentTarget.src.endsWith(FALLBACK)) e.currentTarget.src = FALLBACK; }} />;
const money = n => "₹" + Number(n).toLocaleString("en-IN");

function Provider({ children }) {
  const [user, setUser] = useState(localStorage.getItem("username"));
  const [cart, setCart] = useState([]); const [wish, setWish] = useState([]); const [toast, setToast] = useState(null);
  const say = (msg, bad) => { setToast({ msg, bad }); setTimeout(() => setToast(null), 3000); };
  const refresh = useCallback(async () => {
    if (!localStorage.getItem("token")) { setCart([]); setWish([]); return; }
    try { setCart((await api.get("/cart/")).data); setWish((await api.get("/wishlist/")).data); } catch { /* token expired */ }
  }, []);
  useEffect(() => { refresh(); }, [user, refresh]);
  const auth = d => { localStorage.setItem("token", d.token); localStorage.setItem("username", d.username); setUser(d.username); };
  const logout = async () => { try { await api.post("/auth/logout/"); } catch {} localStorage.clear(); setUser(null); };
  const act = async (fn, ok) => { try { await fn(); say(ok); await refresh(); } catch (e) { say(e.response?.status === 401 ? "Log in first." : errText(e), true); } };
  return <Ctx.Provider value={{ user, cart, wish, say, auth, logout, act, refresh }}>{children}
    {toast && <div className={"toast" + (toast.bad ? " bad" : "")} role="status">{toast.msg}</div>}</Ctx.Provider>;
}

function Nav() {
  const { user, cart, wish, logout } = useApp(); const nav = useNavigate(); const [cats, setCats] = useState([]); const [q, setQ] = useState("");
  useEffect(() => { api.get("/categories/").then(r => setCats(r.data)).catch(() => {}); }, []);
  return <header><div className="nav">
    <Link to="/" className="brand" aria-label="Bazaro home">
      <span className="brand-icon" aria-hidden="true">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="6" width="12" height="8" rx="1.5" fill="#14213D"/>
          <path d="M5 6V4.5a3 3 0 0 1 6 0V6" stroke="#14213D" strokeWidth="1.5" strokeLinecap="round"/>
          <rect x="6" y="9" width="4" height="2.5" rx="1" fill="#F5A623"/>
        </svg>
      </span>
      <span className="brand-word">Bazar<span className="brand-dot">o</span></span>
    </Link>
    <form className="search" role="search" onSubmit={e => { e.preventDefault(); nav(`/?q=${encodeURIComponent(q)}#products`); }}>
      <input aria-label="Search products" placeholder="Search products and crafts" value={q} onChange={e => setQ(e.target.value)} /><button>Search</button></form>
    <nav><Link to="/wishlist">Wishlist ({wish.length})</Link><Link to="/cart">Cart ({cart.reduce((s, i) => s + i.quantity, 0)})</Link>
      {user ? <><Link to="/orders">Orders</Link><button className="link" onClick={logout}>Log out ({user})</button></> : <Link to="/login">Log in</Link>}</nav></div>
    <div className="cats">{cats.map(c => <Link key={c.id} to={`/?category=${c.slug}#products`}>{c.name}</Link>)}</div></header>;
}

function Card({ p }) {
  const { act, wish } = useApp(); const liked = wish.find(w => w.product.id === p.id);
  return <article className="card"><div className="imgwrap"><Link to={`/products/${p.id}`} className="ph" aria-label={`View ${p.name}`}><Img src={p.gallery?.[0] || p.image} alt={p.name} /></Link>
    <button className="heart" aria-label={liked ? "Remove from wishlist" : "Save to wishlist"} onClick={() => act(() => liked ? api.delete(`/wishlist/${liked.id}/`) : api.post("/wishlist/", { product_id: p.id }), liked ? "Removed from wishlist" : "Saved to wishlist")}>{liked ? "♥" : "♡"}</button>
    {!p.in_stock && <span className="tag">Sold out</span>}</div>
    <div className="cbody"><p className="muted sm">{p.category_name}</p><h3><Link to={`/products/${p.id}`} className="plain">{p.name}</Link></h3>
      <p className="muted sm">★ {p.rating} · <span className={p.in_stock ? "ok" : "bad-t"}>{p.in_stock ? `${p.stock} in stock` : "Out of stock"}</span></p>
      <div className="buy"><span className="price">{money(p.price)}</span><button disabled={!p.in_stock} onClick={() => act(() => api.post("/cart/", { product_id: p.id, quantity: 1 }), "Added to cart")}>+ Add</button></div></div></article>;
}

function Home() {
  const [sp, setSp] = useSearchParams(); const key = sp.toString();
  const f = { q: sp.get("q") || "", category: sp.get("category") || "", ordering: sp.get("ordering") || "newest", in_stock: sp.get("in_stock") || "", min_rating: sp.get("min_rating") || "" };
  const [cats, setCats] = useState([]); const [shops, setShops] = useState([]); const [feat, setFeat] = useState([]); const [data, setData] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { api.get("/categories/").then(r => setCats(r.data)).catch(() => {}); api.get("/shops/").then(r => setShops(r.data)).catch(() => {});
    api.get("/products/", { params: { featured: "true" } }).then(r => setFeat(r.data.results)).catch(() => {}); }, []);
  useEffect(() => { setData(null); const t = setTimeout(() => api.get("/products/", { params: f }).then(r => { setData(r.data); setErr(""); }).catch(e => setErr(errText(e))), 250); return () => clearTimeout(t); }, [key]);
  useEffect(() => { if (window.location.hash === "#products") setTimeout(() => document.getElementById("products")?.scrollIntoView(), 80); }, [key]);
  const set = k => e => { const n = new URLSearchParams(sp); const v = e.target.type === "checkbox" ? (e.target.checked ? "true" : "") : e.target.value; v ? n.set(k, v) : n.delete(k); setSp(n, { replace: true }); };
  const total = cats.reduce((s, c) => s + c.product_count, 0);
  return <main><section className="hero"><div><h1>Discover Something Special, Right Around the Corner.</h1>
      <p>Shop everyday essentials, handcrafted treasures, and unique finds from the local businesses you love.</p>
      <div className="row"><a className="btn" href="#products">Explore products</a>{shops[0] && <Link className="btn ghost" to={`/shops/${shops[0].id}`}>Visit a local shop</Link>}</div>
      <div className="stats"><div><b>{shops.length}</b><span>Local shops</span></div><div><b>{total}</b><span>Products</span></div><div><b>{cats.length}</b><span>Categories</span></div></div></div>
    <div className="herophoto"><Img src={shops.find(s => s.image)?.image} alt="" /></div></section>
    <h2>Shop by category</h2><div className="tiles">{cats.map(c => <Link key={c.id} to={`/?category=${c.slug}#products`} className="tile"><Img src={c.image} alt="" /><b>{c.name}</b><span>{c.product_count} items</span></Link>)}</div>
    <h2>Neighborhood spotlight</h2><div className="spot">{shops.map(s => <Link key={s.id} to={`/shops/${s.id}`} className="shopcard"><Img src={s.image} alt="" /><div><b>{s.name}</b><span>{s.locality} · ★ {s.rating}</span><p>{s.tagline}</p><u>View shop catalog ({s.product_count})</u></div></Link>)}</div>
    {!!feat.length && <><h2>Featured essentials</h2><div className="grid">{feat.slice(0, 4).map(p => <Card key={p.id} p={p} />)}</div></>}
    <section className="banner"><div><h2>Support your neighborhood makers</h2><p>Every order goes straight to a local seller on Bazaro.</p></div><a className="btn gold" href="#products">Shop now</a></section>
    <section className="why">{[["Buy local", "Products come from named shops in your area."], ["Live stock", "Availability is shown as it changes, so you don’t order what isn’t there."], ["Secure payment", "Pay through Razorpay. We never see your card details."], ["Clear pricing", "The total is calculated on the server at checkout."]].map(([t, d]) => <div key={t}><b>{t}</b><p>{d}</p></div>)}</section>
    <h2 id="products">All products</h2><div className="filters"><input aria-label="Search" placeholder="Search products" value={f.q} onChange={set("q")} />
      <select aria-label="Category" value={f.category} onChange={set("category")}><option value="">All categories</option>{cats.map(c => <option key={c.id} value={c.slug}>{c.name}</option>)}</select>
      <select aria-label="Sort" value={f.ordering} onChange={set("ordering")}><option value="newest">Newest</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option><option value="popular">Most popular</option><option value="rating">Top rated</option></select>
      <select aria-label="Minimum rating" value={f.min_rating} onChange={set("min_rating")}><option value="">Any rating</option><option value="4">4★ and up</option></select>
      <label><input type="checkbox" checked={!!f.in_stock} onChange={set("in_stock")} /> In stock</label></div>
    {err && <p className="bad-t">{err}</p>}{!data && !err && <p>Loading…</p>}
    {data && !data.results.length && <p className="empty">No products match. Clear a filter or try another search.</p>}
    <div className="grid">{data?.results.map(p => <Card key={p.id} p={p} />)}</div>{data?.next && <p className="muted">Showing the first {data.results.length} of {data.count}. Refine your search to see others.</p>}</main>;
}

function Shop() {
  const { id } = useParams(); const [s, setS] = useState(null); const [items, setItems] = useState(null); const [err, setErr] = useState("");
  useEffect(() => { setS(null); setItems(null); setErr(""); window.scrollTo(0, 0);
    api.get(`/shops/${id}/`).then(r => setS(r.data)).catch(() => setErr("We couldn’t find this shop."));
    api.get("/products/", { params: { shop: id } }).then(r => setItems(r.data.results)).catch(() => setItems([])); }, [id]);
  if (err) return <main className="narrow"><p className="empty">{err}</p><Link to="/">Back to home</Link></main>;
  if (!s) return <main><p>Loading…</p></main>;
  return <main><nav className="crumbs"><Link to="/">Home</Link> › <span>{s.name}</span></nav><div className="shophead"><Img src={s.image} alt={s.name} /><div><h1>{s.name}</h1><p className="muted">{s.locality} · ★ {s.rating}</p><p>{s.tagline}</p></div></div>
    {!items && <p>Loading…</p>}{items && !items.length && <p className="empty">This shop has no products listed yet.</p>}<div className="grid">{items?.map(p => <Card key={p.id} p={p} />)}</div></main>;
}

function Detail() {
  const { id } = useParams(); const { act, wish } = useApp();
  const [p, setP] = useState(null); const [sim, setSim] = useState(null); const [err, setErr] = useState(""); const [qty, setQty] = useState(1); const [pic, setPic] = useState(0);
  useEffect(() => {
    setP(null); setSim(null); setErr(""); setQty(1); setPic(0); window.scrollTo(0, 0);
    api.get(`/products/${id}/`).then(r => setP(r.data)).catch(e => setErr(e.response?.status === 404 ? "We couldn't find this product. It may have been removed." : errText(e)));
    api.get(`/products/${id}/similar/`).then(r => setSim(r.data)).catch(() => setSim([]));
  }, [id]);
  if (err) return <main className="narrow"><p className="empty">{err}</p><p><Link to="/">Back to products</Link></p></main>;
  if (!p) return <main><p>Loading…</p></main>;
  const liked = wish.find(w => w.product.id === p.id); const pics = p.gallery?.length ? p.gallery : [null];
  return <main><nav className="crumbs" aria-label="Breadcrumb"><Link to="/">Home</Link> › <Link to={`/?category=${p.category_slug}#products`}>{p.category_name}</Link> › <span>{p.name}</span></nav>
    <div className="detail"><div><div className="big"><Img src={pics[pic]} alt={p.name} /></div>
      {pics.length > 1 && <div className="thumbs">{pics.map((u, i) => <button key={i} className={"thumb" + (i === pic ? " on" : "")} aria-label={`Photo ${i + 1}`} onClick={() => setPic(i)}><Img src={u} /></button>)}</div>}</div>
      <div><h1>{p.name}</h1><p className="muted">{p.category_name} · ★ {p.rating}{p.shop && <> · Sold by <Link to={`/shops/${p.shop}`}>{p.shop_name}</Link></>}</p><p className="price big-price">{money(p.price)}</p>
        <p className={p.in_stock ? "ok" : "bad-t"}>{p.in_stock ? `In stock (${p.stock} available)` : "Out of stock"}</p><p>{p.description}</p>
        <label className="qty">Quantity<input type="number" min="1" max={Math.max(p.stock, 1)} value={qty} disabled={!p.in_stock} onChange={e => setQty(Math.max(1, Math.min(p.stock, Number(e.target.value) || 1)))} /></label>
        <div className="row"><button disabled={!p.in_stock} onClick={() => act(() => api.post("/cart/", { product_id: p.id, quantity: qty }), "Added to cart")}>Add to cart</button>
          <button className="ghost" onClick={() => act(() => liked ? api.delete(`/wishlist/${liked.id}/`) : api.post("/wishlist/", { product_id: p.id }), liked ? "Removed from wishlist" : "Saved to wishlist")}>{liked ? "Remove from wishlist" : "Add to wishlist"}</button></div>
        <p><Link to="/">← Continue shopping</Link></p></div></div>
    <h2>You may also like</h2>{!sim && <p>Loading…</p>}{sim && !sim.length && <p className="empty">No similar products yet.</p>}
    <div className="grid">{sim?.map(s => <Card key={s.id} p={s} />)}</div></main>;
}

function Login() {
  const { auth, say } = useApp(); const nav = useNavigate(); const [reg, setReg] = useState(false); const [v, setV] = useState({ username: "", password: "" });
  const go = async e => { e.preventDefault(); try { auth((await api.post(reg ? "/auth/register/" : "/auth/login/", v)).data); nav("/"); } catch (x) { say(errText(x), true); } };
  return <main className="narrow"><h2>{reg ? "Create your account" : "Log in"}</h2><form onSubmit={go}>
    <label>Username<input required value={v.username} onChange={e => setV({ ...v, username: e.target.value })} /></label>
    <label>Password<input required type="password" minLength={8} value={v.password} onChange={e => setV({ ...v, password: e.target.value })} /></label>
    <button>{reg ? "Create account" : "Log in"}</button></form>
    <button className="link" onClick={() => setReg(!reg)}>{reg ? "I already have an account" : "New here? Create an account"}</button></main>;
}

function Cart() {
  const { cart, act, user } = useApp(); const nav = useNavigate(); const total = cart.reduce((s, i) => s + i.quantity * i.product.price, 0);
  if (!user) return <main className="narrow"><p className="empty">Log in to see your cart.</p></main>;
  if (!cart.length) return <main className="narrow"><p className="empty">Your cart is empty. <Link to="/">Browse products</Link></p></main>;
  return <main className="narrow"><h2>Your cart</h2>{cart.map(i => <div className="line" key={i.id}><span>{i.product.name}</span>
    <input type="number" min="1" max={i.product.stock} aria-label="Quantity" value={i.quantity} onChange={e => act(() => api.patch(`/cart/${i.id}/`, { quantity: e.target.value }), "Cart updated")} />
    <span>{money(i.quantity * i.product.price)}</span><button className="ghost" onClick={() => act(() => api.delete(`/cart/${i.id}/`), "Removed")}>Remove</button></div>)}
    <p className="price">Total: {money(total)}</p><button onClick={() => nav("/checkout")}>Checkout</button></main>;
}

function Checkout() {
  const { say, refresh } = useApp(); const nav = useNavigate(); const [addrs, setAddrs] = useState([]); const [sel, setSel] = useState("");
  const blank = { full_name: "", phone: "", line1: "", city: "", state: "", pincode: "" }; const [a, setA] = useState(blank);
  const load = () => api.get("/addresses/").then(r => { setAddrs(r.data); if (r.data[0]) setSel(String(r.data[0].id)); });
  useEffect(() => { load(); }, []);
  const addAddr = async e => { e.preventDefault(); try { await api.post("/addresses/", a); setA(blank); load(); } catch (x) { say(errText(x), true); } };
  const pay = async () => {
    try {
      const order = (await api.post("/orders/", { address_id: sel })).data; await refresh();
      const init = (await api.post("/payments/initiate/", { order_id: order.id })).data;
      if (init.demo) { if (!window.confirm("DEMO payment mode: no real gateway. Mark this order as paid?")) { say("Payment cancelled. Order is pending.", true); return nav("/orders"); }
        await api.post("/payments/verify/", { order_id: order.id, razorpay_payment_id: "demo_pay", demo_confirm: true }); say("Demo payment recorded"); return nav("/orders"); }
      if (!window.Razorpay) { const s = document.createElement("script"); s.src = "https://checkout.razorpay.com/v1/checkout.js"; document.body.appendChild(s); await new Promise(r => (s.onload = r)); }
      new window.Razorpay({ key: init.key, amount: init.amount, currency: "INR", order_id: init.razorpay_order_id, name: "Bazaro",
        handler: async r => { try { await api.post("/payments/verify/", { order_id: order.id, ...r }); say("Payment successful"); } catch (x) { say(errText(x), true); } nav("/orders"); },
        modal: { ondismiss: () => { say("Payment cancelled. Order is pending.", true); nav("/orders"); } } }).open();
    } catch (x) { say(errText(x), true); }
  };
  return <main className="narrow"><h2>Checkout</h2><h3>Shipping address</h3>
    {addrs.map(x => <label key={x.id} className="radio"><input type="radio" checked={sel === String(x.id)} onChange={() => setSel(String(x.id))} /> {x.full_name}, {x.line1}, {x.city} {x.pincode}</label>)}
    <form onSubmit={addAddr}>{Object.keys(blank).map(k => <label key={k}>{k.replace("_", " ")}<input required value={a[k]} onChange={e => setA({ ...a, [k]: e.target.value })} /></label>)}<button className="ghost">Save address</button></form>
    <button disabled={!sel} onClick={pay}>Place order and pay</button></main>;
}

function Orders() {
  const [o, setO] = useState(null); useEffect(() => { api.get("/orders/").then(r => setO(r.data.results)).catch(() => setO([])); }, []);
  if (!o) return <main className="narrow"><p>Loading…</p></main>;
  return <main className="narrow"><h2>Your orders</h2>{!o.length && <p className="empty">No orders yet.</p>}
    {o.map(x => <div className="order" key={x.id}><b>Order #{x.id}</b> · {x.status} · {money(x.total)}<ul>{x.items.map((i, k) => <li key={k}>{i.quantity} × {i.name} @ {money(i.price)}</li>)}</ul><small>{x.shipping_address}</small></div>)}</main>;
}

function Wishlist() {
  const { wish } = useApp();
  return <main><h2>Wishlist</h2>{!wish.length && <p className="empty">Nothing saved yet.</p>}<div className="grid">{wish.map(w => <Card key={w.id} p={w.product} />)}</div></main>;
}

function Footer() {
  return <footer>
    <p style={{fontWeight:700,fontSize:"1.05rem",marginBottom:".25rem"}}>
      <span style={{color:"var(--ink)"}}>Bazar</span><span style={{color:"var(--saffron)"}}>o</span>
    </p>
    <p style={{margin:0}}>The Local Market, Reimagined.</p>
    <p style={{margin:".5rem 0 0",fontSize:".85rem"}}>© {new Date().getFullYear()} Bazaro. All rights reserved.</p>
  </footer>;
}

export default function App() {
  return <Provider><Nav /><Routes><Route path="/" element={<Home />} /><Route path="/products/:id" element={<Detail />} /><Route path="/shops/:id" element={<Shop />} /><Route path="/login" element={<Login />} /><Route path="/cart" element={<Cart />} />
    <Route path="/checkout" element={<Checkout />} /><Route path="/orders" element={<Orders />} /><Route path="/wishlist" element={<Wishlist />} /></Routes>
    <Footer /></Provider>;
}
