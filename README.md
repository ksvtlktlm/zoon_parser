
# Парсер для сбора данных о ЛПУ Краснодара

### Описание
Парсер предназначен для сбора данных с сайта https://zoon.ru/ про ЛПУ Краснодара. Он собирает название ЛПУ, ссылку на страницу на https://zoon.ru/, адрес, ссылку на сайт, телефон(ы), ссылки на социальные сети.

### Подход
Для навигации по сайту использовался Selenium для имитации действий пользователя, таких как прокрутка страницы и взаимодействие с динамическими элементами. Ключевые элементы (например, кнопка "Показать больше") определялись с помощью уникальных классов. Для их извлечения и кликов применялись методы find_element и ActionChains.

Чтобы обеспечить надежность работы, использовался цикл while True для последовательного нажатия на кнопку загрузки, с обработкой ситуаций, когда элементы становятся недоступными (путем обработки исключений). Время ожидания обеспечивалось через time.sleep и неявных ожиданий WebDriverWait для динамического ожидания загрузки элементов.

Данные со страницы извлекались с помощью BeautifulSoup, который парсит сохраненный HTML-код. Нужные данные извлекались через их уникальные атрибуты. Для предотвращения ошибок использовалась обработка исключений.
 
Также для снижения нагрузки на сервер и облечения работы исходная страница source.html была сохранена в папке проекта, а ссылки на страницы ЛПУ зафиксированы в файл links.txt. Результат с готовыми данными сохранен в файле result.json.

### Трудности
1. _Проблемы с доступом к сайту_: Сайт периодически возвращал ошибки (например, 503). _Решение_: реализованы повторные попытки запросов с использованием Retry из библиотеки urllib3.
2. _Загрузка динамических данных_: Для получения полной страницы использовалась имитация действий пользователя через Selenium (прокрутка, нажатие кнопки "Показать еще", переход между страницами). _Решение_: изучение документации, добавление обработки исключений с помощью try-except и использование задержек для стабильной работы.
3. _Парсинг ссылок с перенаправлением_: Ссылки на веб-сайты и социальные сети содержали параметры с редиректом. _Решение_: использованы функции unquote из библиотеки urllib и split() для корректного извлечения URL.
4. _Отсутствие некоторых данных_: На страницах некоторых карточек отсутствовали элементы. _Решение_: добавлена обработка исключений через try-except, что позволило пропускать недоступные данные без остановки работы.

### Результаты
Собранные данные были сохранены в список словарей и загружены в файл result.json.