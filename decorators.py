def review_paper_error_log_decorator(func):
  def wrapper(*args,**kwargs):
    try:
      return func(*args,**kwargs)
    except:
      pass
      # error_txt = 'review_paper problem in ' + str(args[1].pdf_path) + '\n'
      # with open(args[0].path_errors_log + 'review_paper_errors_log.txt', 'a') as f:
      #     f.write(error_txt)
  return wrapper

def paper_reading_error_log_decorator(func):
  def wrapper(*args,**kwargs):
    try:
      func(*args,**kwargs)
    except:
      pass
      # error_txt = 'paper reading problem in ' + str(args[1]) + '\n'
      # with open(args[0].path_errors_log + 'paper_reading_errors_log.txt', 'a') as f:
      #     f.write(error_txt)
  return wrapper

def update_naimai_dois(func):
  def wrapper(*args,**kwargs):
    func(*args,**kwargs)
    if args[1]:
      print('>> Updating naimai dois.. TO RECTIFY ..')
      print('LEN : ', len(args[0].titles))
      # args[0].update_naimai_dois()
      # print('Done !')

  return wrapper