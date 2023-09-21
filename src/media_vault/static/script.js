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
    console.log("-->");
}

function previousPage() {
    console.log("<--");
}

document.addEventListener('keyup', (event) => {
    console.log(event.key);
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
var xUp = null;
var yUp = null;

function handleTouchStart(evt) {
    const firstTouch = evt.touches[0];
    xDown = firstTouch.clientX;
    yDown = firstTouch.clientY;
};

function handleTouchMove(evt) {
    const lastTouch = evt.touches[0];
    xUp = lastTouch.clientX;
    yUp = lastTouch.clientY;
}

function handleTouchEnd(evt) {
    var xDiff = xDown - xUp;
    var yDiff = yDown - yUp;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {/*most significant*/
        if (xDiff > 0) {
            /* right swipe */
        } else {
            /* left swipe */
        }
    } else {
        if (yDiff > 0) {
            /* down swipe */
        } else {
            /* up swipe */
        }
    }
}

if (document.getElementById('item') != null) {
    document.addEventListener('touchstart', handleTouchStart, false);
    document.addEventListener('touchmove', handleTouchMove, false);
    document.addEventListener('touchend', handleTouchEnd, false);
}
