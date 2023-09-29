let contentWrapper = document.getElementById("content-grid");

function loadLazyThumbs() {
    let lazyThumbs = document.getElementsByClassName("lazy-thumb");
    for (let i = 0; i < lazyThumbs.length; i++) {
        let viewportOffset = lazyThumbs[i].getBoundingClientRect();
        if (viewportOffset.top - 100 < window.innerHeight) {
            lazyThumbs[i].classList.remove("lazy-thumb");
            i--;
        }
    }
}
document.body.onscroll = loadLazyThumbs;
window.onload = loadLazyThumbs;
window.onresize = loadLazyThumbs;

/* ----- ----- ----- ----- ----- ----- -----
 * For changing pages
 * ----- ----- ----- ----- ----- ----- ----- */


function nextPage() {
    meta_elements = document.getElementsByTagName("meta")
    for (let i = 0; i < meta_elements.length; i++) {
        const element = meta_elements[i];
        if (element.getAttribute("name") == "neighbor-next") {
            window.open(element.getAttribute("href"), "_self");
        }
    }
}

function previousPage() {
    meta_elements = document.getElementsByTagName("meta")
    for (let i = 0; i < meta_elements.length; i++) {
        const element = meta_elements[i];
        if (element.getAttribute("name") == "neighbor-previous") {
            window.open(element.getAttribute("href"), "_self");
        }
    }
}

document.addEventListener('keyup', (event) => {
    switch (event.key) {
        case 'ArrowRight':
            nextPage();
            break;
        case 'ArrowLeft':
            previousPage();
            break;
        default:
            break;
    }
});

/* ----- ----- ----- ----- ----- ----- -----
 * Swipe recognition
 * ----- ----- ----- ----- ----- ----- ----- */

var xDown = null;
var yDown = null;

function handleTouchStart(evt) {
    const firstTouch = evt.changedTouches[0];
    xDown = firstTouch.clientX;
    yDown = firstTouch.clientY;
};

function handleTouchEnd(evt) {
    const lastTouch = evt.changedTouches[0];
    var xDiff = xDown - lastTouch.clientX;
    var yDiff = yDown - lastTouch.clientY;
    let threshold = 150;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {/*most significant*/
        if (Math.abs(xDiff) < threshold)
            return;
        if (xDiff > 0) {
            /* right swipe */
            nextPage();
        } else {
            /* left swipe */
            previousPage();
        }
    } else {
        if (Math.abs(yDiff) < threshold)
            return;
        if (yDiff > 0) {
            /* down swipe */
        } else {
            /* up swipe */
        }
    }
}

if (document.getElementById('item') != null) {
    document.addEventListener('touchstart', handleTouchStart, false);
    document.addEventListener('touchend', handleTouchEnd, false);
}
