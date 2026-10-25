// "Get Swiggy Menu" bookmark: click it on a Swiggy restaurant page.
// It asks Swiggy (from your own logged-in browser tab) for the same menu data the page shows,
// saves it as Swiggy_<restaurant id>_<date>.json, then offers to open GitHub to upload it.
(async () => {
  try {
    const match = location.href.match(/restaurantId=(\d+)/) || location.pathname.match(/rest(\d+)/)
      || location.pathname.match(/-(\d+)\/?$/);
    if (!location.hostname.endsWith('swiggy.com') || !match) {
      alert('Open a Swiggy restaurant page first, then click this bookmark.');
      return;
    }
    const id = match[1];
    // Use the delivery location set on Swiggy; fall back to Mumbai
    let lat = '19.0760', lng = '72.8777';
    try {
      const cookie = document.cookie.split('; ').find(c => c.startsWith('userLocation='));
      if (cookie) {
        const loc = JSON.parse(decodeURIComponent(cookie.slice('userLocation='.length)));
        if (loc.lat && loc.lng) { lat = loc.lat; lng = loc.lng; }
      }
    } catch (e) { /* keep the fallback */ }
    const response = await fetch(`/dapi/menu/pl?page-type=REGULAR_MENU&complete-menu=true&lat=${lat}&lng=${lng}&restaurantId=${id}`,
      { credentials: 'include' });
    const text = await response.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = null; }
    if (!response.ok || !data || !data.data) {
      alert(`Swiggy did not send the menu (status ${response.status}). Reload the page, wait for the menu to show, and click again.`);
      return;
    }
    const day = new Date().toISOString().slice(0, 10);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    link.download = `Swiggy_${id}_${day}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    if (confirm(`Menu saved as Swiggy_${id}_${day}.json in your Downloads.\n\nOpen GitHub to upload it and get the Excel?`)) {
      window.open('https://github.com/sachinagarwal94/Swiggy-Menu-Data-Crawler/upload/main/swiggy-json', '_blank');
    }
  } catch (error) {
    alert('Could not get the menu: ' + error.message);
  }
})();
