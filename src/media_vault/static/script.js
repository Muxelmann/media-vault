let contentWrapper = document.getElementById("content-grid");
function loadLazyThumbs() {
    let lazyThumbs = document.getElementsByClassName("lazy-thumb")
    for (let i = 0; i < lazyThumbs.length; i++) {
        let viewportOffset = lazyThumbs[i].getBoundingClientRect();
        if (viewportOffset.top - 100 < window.innerHeight) {
            lazyThumbs[i].classList.remove("lazy-thumb");
            i--;
        }
    }
}
contentWrapper.onscroll = loadLazyThumbs;
window.onload = loadLazyThumbs;
window.onresize = loadLazyThumbs;

var foo = document.getElementById('foo');