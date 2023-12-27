// ip сервера
const ip = 'copift.ru:5000';

// персональный id сессии
var uuid = localStorage.getItem('UUID');
//var uuid = '0ee09b12-af98-49ad-a3dc-9b8cbc186ad5';  // ДОЛЖЕН ПОЛУЧАТЬСЯ ПРИ АВТОРИЗАЦИИ

// количество постов в ленте
var PostCount = 0;

// сколько постов загружается за раз
var step = 10;

// старт скрипта после загрузке окна
window.onload=startPostsLine;


// функция запускающаяся после загрузки окна
function startPostsLine(){
    // проверякм у пользователя наличее uuid
    if (uuid){
        // получаем посты из БД и добавляем их в ленту
        takeUserPosts();
    }else{
        //  если у пользователя нет uuid пересылаем его к авторизации
        window.location.replace("avt.html");
    }
}


// отправляет запрос в БД и принимает его
function takeUserPosts(count = step){
    // создаём запрос
    let url = 'http://' + ip + '/getPostsGroupUser?uuid=' + uuid + '&post_id=' + PostCount + '&count=' + count;

    // принимаем и обрабатываем данные запроса
    fetch(url)
      .then(response => response.json())    // преобразовавем запрос в json
      .then(commits => addPosts(commits));  // передаем json в функцию создания поста
}


// добавляем посты в ленту
function addPosts(commits, lastPost = 0){

    // проверка на превышение кол-ва постов
    if (lastPost < commits.posts.length){
        let line = document.getElementById("posts_line");

        // добавляем пост в html
        line.insertAdjacentHTML('beforeend',
                        '<div>'+
                        // картинка поста
                        '<div class = "img" id = "' + (PostCount + lastPost) +'_img"></div>' +

                        // данные пользователя
                        '<div>' +
                        // аватар пользователя
                        '<div class = "avatar" id = "' + (PostCount + lastPost) +'_avatar"></div>' +
                        // имя пользователя
                        '<div class = "authorName"><p>' + commits.posts[lastPost].user.user_login + '</p></div>' +
                        '</div>' +

                        // част поста содержащая текст
                        // текст поста
                        '<p id="' + commits.posts[lastPost].post.id + '_text" >' + "" + '</p>' +
                        '<div class = "reaction" >' +
                        // счётчик лайков
                        '<p id="' + commits.posts[lastPost].post.id + '_like" >' +
                        commits.posts[lastPost].post.likes + '</p>' +
                        // кнопка лайка
                        '<input onclick="useLike(this)" name="scattering" ' +
                        'value="' + commits.posts[lastPost].post.id + '" ' +
                        'id="' + (PostCount + lastPost) + '" ' +
                        'type="checkbox" ' + checkLike(commits.posts[lastPost].post.is_liked) + ' />' +
                        '<label for="' + (PostCount + lastPost) + '" ' +
                        'class="label_scattering"></label>'+
                        '</div>' +

                        // часть поста связанная с управлением своими постами
                        // кнопка изменения поста
                        '<button onclick="changePost(this)" '+
                        'value="' + commits.posts[lastPost].post.id + '" ' +
                        'id="' + (PostCount + lastPost) + '" ' +
                        '> изменить пост </button>' +
                        // кнопка удаления поста
                        '<button onclick="deletePost(this)" '+
                        'value="' + commits.posts[lastPost].post.id + '" ' +
                        'id="' + (PostCount + lastPost) + '" ' +
                        '> удалить пост </button>' +
                        '</div>'
                       );


        // Добавление текст
        let textLine = document.getElementById(commits.posts[lastPost].post.id + "_text");

        // добавляем пост в html
        textLine.innerText = "" + commits.posts[lastPost].post.Text;


         // Добывление картинки
        // создаем пустую картинку
        var img = new Image();

        // добавляем картинке ссылку на изображение
        img.src = commits.posts[lastPost].post.image_link;

        // здесь добавляем готовую картинку в html
        document.getElementById((PostCount + lastPost) +'_img').appendChild(img);

        // Добывление аватара
        // создаем пустую картинку
        var avatar = new Image();

        // добавляем картинке ссылку на изображение
        avatar.src = commits.posts[lastPost].user.avatarLink;

        // здесь добавляем готовую картинку в html
        document.getElementById((PostCount + lastPost) +'_avatar').appendChild(avatar);

        // БЫСТРЫЙ НО НЕ КРАСИВЫЙ СПОСОБ СОЗДАТЬ ЛЕНТУ
        addPosts(commits, lastPost+1);


        // запоминаем id последнего поста в ленте
        if (lastPost + 1 == commits.posts.length){
            PostCount += step;
        }
    }
}


// проверяем стоит ли лайк у данного поста
function checkLike(isLiked){
    if (isLiked){
        return 'checked';
    }else{
        return '';
    }
}


// отправка запроса при нажатии лайка
function useLike(elem){
    //console.log(elem.checked);
    if (elem.checked){
        // если поставили лайк
        let url = 'http://' + ip + '/setLike?uuid=' + uuid + '&post_id=' + elem.value;
        fetch(url)
            .then(changLikeValue(elem.value, 1));
    }else{
        // если убрали лайк
        let url = 'http://' + ip + '/downLike?uuid=' + uuid + '&post_id=' + elem.value;
        fetch(url)
            .then(changLikeValue(elem.value, -1));
    }
}


// функция изменения значения лайка
function changLikeValue(post_id, x){
    let like = document.getElementById('' + post_id + '_like');
    let val = Number(like.innerText) + x;
    like.innerText = val;
}


// функция изменения поста
function changePost(elem){
    // запоминаем id изменяемого поста
    localStorage.setItem('changePost_id', elem.value);

    // переходим на страницу редактиронания
    window.location.replace("change_post.html");
}


// функция удаления поста из общей ленты
async function deletePost(elem){
    console.log("попытка удаления поста" + elem.value);

    // оптправляем запрос
    let response = await fetch('http://' + ip + '/deletePost?uuid=' + uuid + '&post_id=' + elem.value);

    // если прищёл правильный ответ
    if (response.ok){
        toggle = true;
        console.log("пост удален");
        location.reload();
    }else{
        toggle = true;
        console.log("ошибка в удалении поста");
    }
}


