const messages = [
  "🔥 Новинка в продаже!",
  "⚡ Скидка на популярный товар!",
  "🎉 Не пропусти акцию!",
  "🛠 Бесплатная доставка сегодня!"
];

function showNotification() {
  const message = messages[Math.floor(Math.random() * messages.length)];
  const notif = document.createElement("div");
  notif.className = "notification";
  notif.innerText = message;
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 5000);
}

setInterval(showNotification, 3600000); // 1 час
