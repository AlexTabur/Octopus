from multiprocessing import Process, Array, Value

from worker_image import worker_f

# , worker_f_2

if __name__ == '__main__':
    from main import main_func

    '''
    top view:
    points   0,   1,   2,   3,   4,     5
           0 1, 2 3, 4 5, 6 7, 8 9, 10 11
    
    '''
    # Очень важные массивы
    # td это вид сверху
    td = Array('f', [1000, 1000, 1000, 1200, 1200, 1000, 1200, 1200, 1000, 2000, 1200, 2000, 1000, 1000])
    # sv вид сбоку
    sv = Array('f', [1200, 2000, 1000, 1000, 1000, 1200, 1200, 1000, 1200, 1200, 1000, 2000, 1200, 2000])
    # тут, сохранение состояний фокуса
    focus_side_view_l = Value('i', 0)
    focus_side_view_r = Value('i', 0)
    moving_right = Value('i', 0)
    # С пунктом (массивом) pos тоже всё понятно, сюда просто
    # записываются значения состояний(положение) позиционеров
    pos = Array('f', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    p1 = Process(target=main_func, args=(td, sv, pos, focus_side_view_l, focus_side_view_r, moving_right))
    p2 = Process(target=worker_f, args=(td, 0, "topdown", pos, focus_side_view_l, focus_side_view_r, moving_right))
    p3 = Process(target=worker_f, args=(sv, 1, "side view", pos, focus_side_view_l, focus_side_view_r, moving_right))
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()
