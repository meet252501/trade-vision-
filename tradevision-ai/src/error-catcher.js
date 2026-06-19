window.addEventListener('error', (event) => {
  document.body.innerHTML = '<div style="color:red;padding:20px;z-index:9999;position:absolute;top:0;left:0;background:black;">' + event.message + '<br><pre>' + (event.error && event.error.stack) + '</pre></div>';
});
