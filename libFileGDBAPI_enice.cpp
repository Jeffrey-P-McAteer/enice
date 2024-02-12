
#include <string>
#include <iostream>

#include <FileGDBAPI.h>

extern "C" void run_gdb_create_test() {
  fgdbError   hr;
  FileGDBAPI::Geodatabase geodatabase;

  if ((hr = FileGDBAPI::DeleteGeodatabase(L"out/Gdbtest01.gdb")) != S_OK) {
    std::cout << "An error occurred while deleting the geodatabase at out/Gdbtest01.gdb. hr = " << hr << std::endl;
  }

  if ((hr = FileGDBAPI::CreateGeodatabase(L"out/Gdbtest01.gdb", geodatabase)) != S_OK)
  {
    std::cout << "An error occurred while creating the geodatabase at out/Gdbtest01.gdb. hr = " << hr << std::endl;
    // ErrorInfo::GetErrorDescription(hr, errorText);
    // std::cout << errorText << "(" << hr << ")." << std::endl;
    return;
  }
  std::cout << "The geodatabase has been created at out/Gdbtest01.gdb" << std::endl;

  // Create a feature class within the geodatabase


  FileGDBAPI::CloseGeodatabase(geodatabase);

}
