all_folder_links = document.getElementById("nav-tree").getElementsByClassName("f");

for (let i = 0; i < all_folder_links.length; i++) {
    const link = all_folder_links[i];
    
    if (link.nextElementSibling != null) {
        all_folder_links[i].onclick = function (event) {
            event.srcElement.classList.toggle("opened");
        }
        all_folder_links[i].ondblclick = function (event) {
            href = event.srcElement.getAttribute("href");
            if (href != null) {
                window.location.href = href;
            }
        }
    } else {
        all_folder_links[i].onclick = function (event) {
            href = event.srcElement.getAttribute("href");
            if (href != null) {
                window.location.href = href;
            }
        }
    }
    
}


contentWrapper = document.getElementById("thumb-wrapper");
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