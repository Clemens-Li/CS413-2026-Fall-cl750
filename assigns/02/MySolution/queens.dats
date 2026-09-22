(* ATS2 source translated by queens_lambda0.py; count all n-queens boards. *)
fun safe(xs: list0(int), col: int, d: int): bool =
  case+ xs of | nil0() => true | cons0(x, xs1) => x != col && col-x != d && x-col != d && safe(xs1,col,d+1)
fun search(n: int, row: int, xs: list0(int)): int = if row = n then 1 else trycol(n,row,xs,0)
and trycol(n: int, row: int, xs: list0(int), col: int): int =
  if col = n then 0 else if safe(xs,col,1) then search(n,row+1,cons0(col,xs))+trycol(n,row,xs,col+1) else trycol(n,row,xs,col+1)
implement main0() = println!(search(8,0,nil0()))