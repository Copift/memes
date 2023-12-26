// ip сервера
const ip = '10.8.0.1:5000';

function auth(){
    var login = document.getElementsByTagName("input")[0];
    var val1 = login.value;
    var password = document.getElementsByTagName("input")[1];
    var val2 = password.value;
    authorization(val1, val2);
}

// получение uuid
async function authorization(login, password){
    // создаём запрос
    let url = 'http://' + ip + '/auth?login=' + login + '&password=' + password;
    // оптправляем запрос
    let response = await fetch(url);

    // если прищёл правильный лответ
    if (response.ok){
        // преобразовываем запрос в json
        let commits = await response.json();

        // достаем uuid из json
        let uuid = commits.uuid;

        // смотрим в json евляется ли юзер админом
        let is_admin = (commits.is_admin);

        // возвращаем готовый uuid
        // отправка данных на другую страницу
        localStorage.setItem('UUID', uuid);
        localStorage.setItem('IS_ADMIN', is_admin);

        document.location='./project1.html'

        // если пришёл ответ с ошибкой
    }else{
        // преобразовываем запрос в json
        let commits = await response.json();

        // выводим сообщение об ошибке
        alert("error " + commits.err_code + "\n" + commits.err);
    }
}
