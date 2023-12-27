// ip сервера
const ip = 'copift.ru:5000';

// персональный id сессии
var uuid = localStorage.getItem('UUID');

// id поста который ма будем редактировать
var  changePost_id = localStorage.getItem('changePost_id');

// переключатель, для ограничения нажатия на кнопку
var toggle = true;

// старт скрипта после загрузке окна
window.onload=startPostChange;

// функция запускающаяся после загрузки окна
function startPostChange(){
    // проверякм у пользователя наличее uuid
    if (!uuid){
        // если у пользователя нет uuid пересылаем его к авторизации
        window.location.replace("avt.html");
    }
    if (!changePost_id){
        // если у пользователя нет changePost_id пересылаем его к блогу
        window.location.replace("project1.html");
    }


    // Загружаем данные старого поста
    // создаём запрос
    let url = 'http://' + ip + '/post/' + changePost_id + '?uuid=' + uuid;

    // принимаем и обрабатываем данные запроса
    fetch(url)
      .then(response => response.json())    // преобразовавем запрос в json
      .then(commits => addInfo(commits));  // передаем json в функцию создания поста
}

// добавить данные поста в редактор
function addInfo(commits){
    //console.log(commits);
    document.getElementById("comment").value += commits.text;
    console.log(commits.text);
    document.getElementById("postImage").setAttribute("src", commits.image_link);
}


// фунция отправки изменённого поста в базу данных
async function sendChangedPost(){
    // проверяем переключатель
    if (toggle){
        console.log("отправка запроса");
        alert("отправка запроса");

        // отключаем возможность отылать пост
        toggle = false;

        // берём в input содержащий текст
        let inputText = document.getElementById("comment");
        // берём в input содержащий файл
        let inputFile = document.querySelector('input[type="file"]');

        let text = inputText.value;
        let file = inputFile.files[0];


        const data = new FormData();
        data.append("uuid", uuid);
        data.append("post_id", changePost_id);
        if (text){
            data.append("text", text);
        }
        if (file){
            data.append("files", file);
        }


        // оптправляем запрос
        let response = await fetch('http://' + ip + '/editPost', {
          method: 'POST',
          body: data
        })

        // если прищёл правильный ответ
        if (response.ok){
            toggle = true;
            console.log("пост изменён");

            // переходим в блог
            document.location='./blog.html';
        }else{
            toggle = true;
            console.log("ошибка в изменении поста");
            alert("ошибка в изменении поста");

            // преобразовываем запрос в json
            let commits = await response.json();

            // выводим сообщение об ошибке
            console.log("error " + commits.err_code + "\n" + commits.err);
        }

    }else{
        alert("подождите, предидущий запрос ещё не отправился");
    }
}


// отображение картинки при её загрузке
function  resetImg(elem){
    if (elem.files && elem.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
          document.getElementById('postImage').setAttribute('src', e.target.result);
        };

        reader.readAsDataURL(elem.files[0]);
  }
}



