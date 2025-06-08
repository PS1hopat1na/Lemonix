function showNotification(msg) {
    let div = document.getElementById('notification-popup');
    if (!div) return;
    div.textContent = msg;
    div.style.display = 'block';
    div.style.opacity = 1;
    setTimeout(() => { div.style.opacity = 0; }, 1400);
}

document.addEventListener('DOMContentLoaded', function() {
    // Для кнопки "добавить в корзину"
    document.querySelectorAll('.add-to-cart-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            let productId = btn.getAttribute('data-product-id');
            fetch(`/add_to_cart/${productId}`, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        let badge = document.querySelector('.cart-count');
                        if (badge) {
                            badge.textContent = data.count;
                            badge.style.display = (data.count > 0) ? 'inline-block' : 'none';
                        }
                        showNotification('Товар добавлен в корзину!');
                    } else {
                        showNotification('Ошибка: войдите в аккаунт!');
                    }
                });
        });
    });

    // Для кнопок удаления товаров из корзины
document.querySelectorAll('.remove-cart-item-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        let cartId = btn.getAttribute('data-cart-id');
        if (!cartId) {
            console.error('Cart ID is missing!');
            return;
        }
        fetch(`/remove_from_cart/${cartId}`, {
            method: 'POST',
            headers: { 
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(res => {
            if (!res.ok) {
                throw new Error('Network response was not ok');
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                let row = btn.closest('tr');
                if (row) row.remove();
                
                let total = document.getElementById('cart-total-value');
                if (total) total.textContent = data.cart_total + " ₽";
                
                let badge = document.querySelector('.cart-count');
                if (badge) {
                    badge.textContent = data.cart_count;
                    badge.style.display = (data.cart_count > 0) ? 'inline-block' : 'none';
                }
                
                if (data.cart_count === 0) {
                    document.querySelector('.cart-page-wrap').innerHTML = '<div class="cart-empty">Корзина пуста</div>';
                }
                showNotification('Товар удалён из корзины!');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Ошибка при удалении товара');
        });
    });
});
document.getElementById('checkout-btn')?.addEventListener('click', function() {
    fetch('/checkout', {
        method: 'POST',
        headers: { 
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Обновляем интерфейс
            document.querySelector('.cart-page-wrap').innerHTML = '<div class="cart-empty">Корзина пуста</div>';
            
            // Показываем чек
            document.getElementById('check-modal').style.display = 'flex';
            
            // Обновляем бейдж корзины
            let badge = document.querySelector('.cart-count');
            if (badge) {
                badge.textContent = '0';
                badge.style.display = 'none';
            }
            
            showNotification('Заказ оформлен!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка при оформлении заказа');
    });
});
    // Модалка чека
    document.getElementById('show-check')?.addEventListener('click', function() {
        document.getElementById('check-modal').style.display = 'flex';
    });
    document.querySelectorAll('.close-check-modal').forEach(btn => {
        btn.onclick = () => { document.getElementById('check-modal').style.display = 'none'; };
    });
});
