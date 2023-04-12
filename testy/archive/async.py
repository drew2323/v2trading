#Asyncio - umoznuje a řídí konkurentni kod (v ramci jednoho vlakna, vice vlaken nebo i procesu - skrz concurrent.futures)

# async si pri definici oznacim funkci, kterou chci asynchronne volat a ve které muze byt dalsi asynchronni volani(await)
# await - označuje mi, že na volanou funkci čekám - pokud je pouzito v tasku pak task vraci pokračování zpět o level výše
# create task(asynchr.funkce) - vtakto zavolám paralelni funkci bez cekani a blok pokracuje dal
# asyncio.wait - ceka na tas
# Here is a list of what you need in order to make your program async:

# Add async keyword in front of your function declarations to make them awaitable.
# Add await keyword when you call your async functions (without it they won’t run).
# Create tasks from the async functions you wish to start asynchronously. Also wait for their finish.
# Call asyncio.run to start the asynchronous section of your program. Only one per thread.
# time.sleep(5) - blokuje, await asyncio.sleep(5) - neblokuje kod(asynchroni task)

import asyncio

#tbd pridat logger

async def makej(pracant, cekani):
    print("pracant ",pracant, "zacal", "bude cekat",cekani,"sekubd")
    await asyncio.sleep(cekani)
    print("pracant ",pracant,"docekal",cekani,"sekund")

async def main():
    print("vstup do funkce main")
    #vytvoreni asynchronnich tasků
    task1 = asyncio.create_task(makej(1,5))
    task2 = asyncio.create_task(makej(2,3))
    task3 = asyncio.create_task(makej(3,1))
    print("tasky jedou - ted jsme v kodu za jejich spustenim - ale pred await.wait")
    #budeme cekat na dokonceni tasků
    await asyncio.wait([task1,task2,task3])
    print("dočekáno na vysledek po volani await.wait")
    print("a ted volani funkce standardním synchro způsobem, kdy cekame na vysledek ")
    #volani funkce standardním synchro způsobem, kdy cekame na vysledek 
    await makej(1,1)
    await makej(2,1)

# hlavni volani - run by mela byt jedna pro jedno vlakno
#asyncio.run(main())


#feature to convert async to sync 
#asyncio.get_event_loop().run_until_complete()  --nebo je tu tento decorator https://github.com/miyakogi/syncer

newfeature = asyncio.run(makej(1,1))

