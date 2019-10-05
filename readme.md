# working time counter v1.0

# Использование
## Режимы работы

Данная программка имеет 2 разных режима работы: ведение журнала и отображение статистики.

## Ведение журнала
При вызове с помощью:
> python3 wtc.py daemon

Производится запись информации о активности системы в журнал.
Рекомендуется добавить эту команду в автозапуск.

## Отображение статистики
При вызове с помощью:
> python3 wtc.py stat

Отображается отработаное время по данным журнала.  
Так же команда stats принимает необязательный флаг -f,
при указании которого программа начинает следить за изменениями
в базе и автоматически обновлять данные на мониторе.

Так же есть возможность просмотреть статистику за
произвольный промежуток времени:
> python3 wtc.py stat 01.01.2019-01.01.2020

или:
> python3 wtc.py stat 01.2019-01.2020

или:
> python3 wtc.py stat 2019-2020

начиная с произвольной даты до сейчас:
> python3 wtc.py stat 01.01.2019-now

за произвольный год, месяц, день:
> python3 wtc.py stat 2019  

> python3 wtc.py stat 07.2019

> python3 wtc.py stat 10.7.2019


# Установка
## Требования к системе
 - linux
 - python 3.7+
 - pip

## Инструкция по установке
1) Разместите файлы программы в произвольной дирректории в полном составе и
с сохранением структуры.

2) Выполните в консоле, находясь в папке с проектом, следующую комманду:
> pip3 install -r requirements/prod.txt

Если комманда завершилась неудачей, то установите необходимые пакеты и
попробуйте снова.