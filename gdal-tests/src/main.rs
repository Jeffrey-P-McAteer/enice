

fn main() -> gdal::errors::Result<()>  {

    println!("gdal --version = {:?}", gdal::version::version_info("--version") );

    let driver = gdal::DriverManager::get_driver_by_name("OpenFileGDB")?;

    // println!("driver = {:?}", driver);

    let mut dataset = driver.create_vector_only("target/GDAL_Geodatabase.gdb")?;

    println!("dataset = {:?}", dataset);



    Ok(())
}
