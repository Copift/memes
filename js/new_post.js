// ip сервера
const ip = 'copift.ru:5000';

// персональный id сессии
var uuid = localStorage.getItem('UUID');
//var uuid = '0ee09b12-af98-49ad-a3dc-9b8cbc186ad5';  // ДОЛЖЕН ПОЛУЧАТЬСЯ ПРИ АВТОРИЗАЦИИ

// переключатель, для ограничения нажатия на кнопку
var toggle = true;

// функция запускающаяся после загрузки окна
function startPostsLine(){
    // проверякм у пользователя наличее uuid
    if (!uuid){
        //  если у пользователя нет uuid пересылаем его к авторизации
        window.location.replace("avt.html");
    }
}


// фунция отправки поста в базу данных
async function sendPost(){
    // проверяем переключатель
    if (toggle){
        console.log("отправка запроса 12345");
        alert("отправка запроса 12345");

        // отключаем возможность отылать пост
        toggle = false;

        // берём в input содержащий текст
        let inputText = document.getElementById("comment");
        // берём в input содержащий файл
        let inputFile = document.querySelector('input[type="file"]');

        let text = inputText.value;
        let file = inputFile.files[0];

        if (text && file){
            const data = new FormData();
            data.append("uuid", uuid);
            data.append("text", text);
            data.append("files", file);

            // оптправляем запрос
            let response = await fetch('http://' + ip + '/uploadPost', {
              method: 'POST',
              body: data
            })

            // если прищёл правильный ответ
            if (response.ok){
                toggle = true;
                console.log("пост создан");

                // переходим в блог
                document.location='./project1.html';
            }else{
                toggle = true;
                alert("ошибка в создании поста");
                console.log("ошибка в создании поста");

                // преобразовываем запрос в json
                let commits = await response.json();

                // выводим сообщение об ошибке
                console.log("error " + commits.err_code + "\n" + commits.err);
            }
        }else{
            toggle = true;
            alert("ошибка в заполнении формы");
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
