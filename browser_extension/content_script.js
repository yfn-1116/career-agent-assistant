// Read current page and send to sidepanel
const pageData = {
  url: window.location.href,
  title: document.title,
  text: document.body.innerText.substring(0, 15000),
  platform: detectPlatform(),
  captured_at: new Date().toISOString()
};

function detectPlatform() {
  const url = window.location.href.toLowerCase();
  if (url.includes('zhipin.com') || url.includes('boss')) return 'boss';
  if (url.includes('liepin.com')) return 'liepin';
  if (url.includes('shixiseng.com')) return 'shixiseng';
  return 'generic';
}

chrome.runtime.sendMessage({type: 'page_data', data: pageData});
