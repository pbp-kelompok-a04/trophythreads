function showToast(message, type = "info", duration = 4000) {
    const toast = document.getElementById("toast-component");
    const icon = document.getElementById("toast-icon");
    const messageElement = document.getElementById("toast-message");
    const progress = document.getElementById("toast-progress");
    const closeButton = document.getElementById("toast-close");

    if (!toast) return;

    let color = "#3b82f6";
    let background = "rgba(204, 224, 255, 0.9)";
    icon.textContent = "ℹ️";
    let colorText = "#000000ff";

    if (type === "success") {
        color = "#16a34a";
        background = "rgba(186, 255, 211, 0.9)";
        icon.textContent = "✅";
    } else if (type === "error") {
        color = "#dc2626";
        background = "rgba(255, 198, 198, 0.9)";
        icon.textContent = "❌";
    } else if (type === "warning") {
        color = "#eab308";
        background = "rgba(255, 243, 206, 0.9)";
        icon.textContent = "⚠️";
    }

    toast.style.backdropFilter = "blur(10px)";
    toast.style.webkitBackdropFilter = "blur(10px)";
    messageElement.textContent = message;
    toast.style.backgroundColor = background;
    messageElement.style.color = colorText;
    progress.style.backgroundColor = color;
    toast.style.border = `1px solid ${color}40`;

    toast.classList.remove("translate-y-[-150%]", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    progress.classList.remove("scale-x-0");
    progress.classList.add("scale-x-100");

    const timeout = setTimeout(() => hideToast(), duration);

    closeButton.onclick = () => {
        clearTimeout(timeout);
        hideToast();
    };

    function hideToast() {
        toast.classList.remove("translate-y-0", "opacity-100");
        toast.classList.add("translate-y-[-150%]", "opacity-0");
        progress.classList.remove("scale-x-100");
        progress.classList.add("scale-x-0");
    }
}