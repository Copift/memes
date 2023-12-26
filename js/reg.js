// ip сервера
const ip = 'copift.ru:5000';

// переключатель, для ограничения нажатия на кнопку
var toggle = true;



// фунция отправки данных для создания нового пользователя
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
        let password  = document.getElementById('password').value;
        let passwordRe = document.getElementById('passwordRe').value;

        // проверяем заполнение всех полей
        if (name && surname && login && birthDate && password && (password == passwordRe)){
            console.log("отправка запроса");
            alert("отправка запроса");

            // объединяем данные для отправления
            const data = new FormData();

            data.append("user_login", login);
            data.append("user_passwd", password);
            data.append("user_name", name);
            data.append("user_surname", surname);
            data.append("date_of_birth", birthDate);

            data.append("files", file);


            // оптправляем запрос
            let response = await fetch('http://' + ip + '/addUser', {
              method: 'POST',
              body: data
            })

            // если прищёл правильный ответ
            if (response.ok){
                toggle = true;
                console.log("юзер создан");
            }else{
                toggle = true;
                alert("ошибка в создании юзера");
                console.log("ошибка в создании юзера");

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
