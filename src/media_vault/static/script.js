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

document.addEventListener("keyup", (event) => {
    switch (event.key) {
        case "ArrowRight":
            nextPage();
            break;
        case "ArrowLeft":
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

if (document.getElementById("item") != null) {
    document.addEventListener("touchstart", handleTouchStart, false);
    document.addEventListener("touchend", handleTouchEnd, false);
}

/* ----- ----- ----- ----- ----- ----- -----
* Drag and Drop for file upload
* ----- ----- ----- ----- ----- ----- ----- */

let mainWrapper = document.getElementById("main-wrapper");
let dropWrapper = document.getElementById("drop-wrapper");
let dropField = document.getElementById("drop-field");
let progressBar = document.getElementById("progress-bar");
let doneIndicator = document.getElementById("done-indicator");
var filesUploaded = 0;
var filesToUpload = 0;

function initializeProgress(numFiles) {
    doneIndicator.classList.add("hidden");
    progressBar.value = 0;
    progressBar.classList.remove("hidden");
    filesToUpload = numFiles;
    filesUploaded = 0;
}

function fileUploadDone() {
    filesUploaded += 1;
    progressBar.value = 100 * filesUploaded / filesToUpload;

    if (filesUploaded == filesToUpload) {
        doneIndicator.classList.remove("hidden");
        setTimeout(() => { location.reload(); }, 3000);
    }
}

function uploadFile(file, url) {
    let formData = new FormData();
    formData.append("file", file);
    fetch(url, {
        method: "POST",
        body: formData
    })
        .then(() => { fileUploadDone(); })
        .catch(() => { });
}

function dropHandler(event) {
    let url = event.target.getAttribute("src");
    if (url == null) {
        return;
    }

    event.preventDefault();
    initializeProgress(event.dataTransfer.files.length);

    if (event.dataTransfer.items) {
        // Use DataTransferItemList interface to access the file(s)
        [...event.dataTransfer.items].forEach((item, i) => {
            // If dropped items aren"t files, reject them
            if (item.kind === "file") {
                const file = item.getAsFile();
                // console.log(`… file[${i}].name = ${file.name}`);
                uploadFile(file, url);
            }
        });
    } else {
        // Use DataTransfer interface to access the file(s)
        [...event.dataTransfer.files].forEach((file, i) => {
            console.log(`… file[${i}].name = ${file.name}`);
        });
    }
}

function dragOverHandler(event) {
    // prevent browser"s default event
    event.preventDefault();
}

function dragEnterHandler(event) {
    // show drop-field when d
    dropWrapper.classList.remove("hidden");
}

function dragLeaveHandler(event) {
    console.log("dragLeave");
    console.log(event);
    dropWrapper.classList.add("hidden");
}

if (mainWrapper != null) {
    mainWrapper.addEventListener("dragenter", dragEnterHandler);
}
if (dropWrapper != null) {
    dropWrapper.addEventListener("dragleave", dragLeaveHandler);
}
if (dropField != null) {
    dropField.addEventListener("drop", dropHandler);
    dropField.addEventListener("dragover", dragOverHandler);
}
