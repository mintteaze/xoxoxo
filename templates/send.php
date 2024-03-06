<html>
<head>
<title>Форма заявки с сайта</title>
</head>
<body>
    <div class="u-clearfix u-sheet u-valign-middle u-sheet-1">
        <div class="u-form u-form-1">
            <form action="send.php" method="POST" class="u-clearfix u-form-spacing-15 u-form-vertical u-inner-form"
                  style="padding: 15px;">
                    <input type="text" placeholder="Имя пользователя" id="name-6797" name="nickname"
                           class="u-input u-input-rectangle u-radius-12" required="">
                    <input type="text" placeholder="Название объекта" id="email-6797" name="object_name"
                           class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="text" placeholder="Регион" id="text-3e10" name="region"
                           class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="text" placeholder="Год построения" id="text-1f3a" name="year"
                           class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="text" placeholder="Значение (местное, региональное, федеральное)" id="text-ed72"
                           name="category" class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="text" placeholder="Вид (памятник, ансамбль, достопримечательное место)" id="text-0e9c"
                           name="type" class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="text" placeholder="Принадлежность к ЮНЕСКО (да, нет)" id="text-5288" name="text"
                           class="u-input u-input-rectangle u-radius-12" required="required">
                    <input type="submit" value="Отправить">
                </div>
            </form>
        </div>
    </div>
<?php
$nick = $_POST['nickname'];
$obj = $_POST['object_name'];
$reg = $_POST['region'];
$year = $_POST['year'];
$cat = $_POST['category'];
$type = $_POST['type'];
$u = $_POST['text'];
$nick = htmlspecialchars($nick);
$obj = htmlspecialchars($obj);
$reg = htmlspecialchars($reg);
$year = htmlspecialchars($year);
$cat = htmlspecialchars($cat);
$type = htmlspecialchars($type);
$u = htmlspecialchars($u);
$nick = urldecode($nick);
$obj = urldecode($obj);
$cat = urldecode($cat);
$reg = urldecode($reg);
$year = urldecode($year);
$type = urldecode($type);
$u = urldecode($u);
$nick = trim($nick);
$obj = trim($obj);
$cat = trim($cat);
$type = trim($type);
$reg = trim($reg);
$year = trim($year);
$u = trim($u);
if (mail("taisiavoshch@mail.ru", "Заявка с сайта", "Имя пользователя:".$nick.". Название объекта: ".$obj." Регион: ".$reg."
Значение: ".$cat." Вид: ".$type." Принадлежность к ЮНЕСКО: ".$u." Год: ".$year.,
"From: taisiavoshch@gmail.com \r\n"))
 {     echo "сообщение успешно отправлено";
} else {
    echo "при отправке сообщения возникли ошибки";
}?>