window.addEventListener("DOMContentLoaded", function(){
    const iframe = document.getElementById("previewFrame");
    const pdfForm = document.getElementById("pdfForm");
    pdfForm.addEventListener("submit", function(e) {
        try {
            const currentUrl = iframe.contentWindow.location.href;
            document.getElementById("current_url").value = currentUrl;
        } catch (err) {
            alert("iframeのURLを取得できません（クロスドメインの可能性）");
            e.preventDefault();
        }
    });
});
