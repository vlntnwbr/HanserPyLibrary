:: URL Book mapping
::  - Was kostet Qualität? (invalid char in filename)
::  - Clinical Neuropathology: Text and Color Atlas (isbn10 & not available)
::  - Technische Probleme lösen mit C/C++ (slash in filename)
::  - Wake Up! (no problems)
::  - Scrum mit User Stories (isbn10 & duplicate)

:: --isbn Book mapping
::  - Clinical Neuropathology: Text and Color Atlas (isbn10 & not available)
::  - Scrum mit User Stories (no problem)
::  - Total berechenbar? (unauthorized)

py -m hanser_py_library.main -f -o ./downloads ^
  https://www.hanser-elibrary.com/doi/book/10.3139/9783446424401 ^
  https://hanser-elibrary.com/isbn/1888799978 ^
  www.hanser-elibrary.com/isbn/9783446423824 ^
  hanser-elibrary.com/isbn/9783446440685 ^
  https://www.hanser-elibrary.com/isbn/3446426604 ^
  --isbn ^
      1-888799-97-8 ^
      9783446450776 ^
      978-3-446-44699-1