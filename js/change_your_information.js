// ip сервера
const ip = 'copift.ru:5000';


// персональный id сессии
var uuid = localStorage.getItem('UUID');

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


    // Загружаем данные старого поста
    // создаём запрос
    let url = 'http://' + ip + '/me?uuid=' + uuid;

    // принимаем и обрабатываем данные запроса
    fetch(url)
      .then(response => response.json())    // преобразовавем запрос в json
      .then(commits => addInfo(commits));  // передаем json в функцию создания поста

    addInfo("commits");
}

// добавить данные поста в редактор
function addInfo(commits){
    //console.log(commits);
    document.getElementById("name").setAttribute("value", commits.user_name);
    document.getElementById("surname").setAttribute("value", commits.user_surname);
    document.getElementById("login").setAttribute("value", commits.user_login);
    document.getElementById("birthDate").setAttribute("value", ""+commits.date_of_birth);

    document.getElementById("userAvatar").setAttribute("src", commits.user_img);
}


// фунция отправки данных для изменения информации о пользователе
async function sendNewUsrerInfo(){
    // проверяем переключатель
    if (toggle){

        // временно отключаем возможность отылать запрос
        toggle = false;

        // берём в input содержащий файл
        let inputFile = document.querySelector('input[type="file"]');

        let file = inputFile.files[0];

        let name = document.getElementById('name').value;
        let surname = document.getElementById('surname').value;
        let login  = document.getElementById('login').value;
        let birthDate  = document.getElementById('birthDate').value;

        // проверяем заполнение всех полей
        if (name && surname && login && birthDate){
            console.log("отправка запроса");
            alert("отправка запроса");

            // объединяем данные для отправления
            const data = new FormData();

            data.append("uuid", uuid);
            data.append("user_login", login);
            data.append("user_name", name);
            data.append("user_surname", surname);
            data.append("date_of_birth", birthDate);

            if (file){
                data.append("files", file);
            }

            // оптправляем запрос
            let response = await fetch('http://' + ip + '/editUser', {
              method: 'POST',
              body: data
            })

            // если прищёл правильный ответ
            if (response.ok){
                toggle = true;
                console.log("данные пользователя изменены");

                // переходим в блог
                document.location='./blog.html';
            }else{
                toggle = true;
                alert("ошибка в изменении данных пользователя");
                console.log("ошибка в изменении данных пользователя");

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
          document.getElementById('userAvatar').setAttribute('src', e.target.result);
        };

        reader.readAsDataURL(elem.files[0]);
  }
}


