use std::io::Result;
use std::path::Path;

fn main() -> Result<()> {
    println!("cargo:rerun-if-changed=../proto");

    // 确保 proto 目录存在
    let proto_dir = Path::new("../proto");
    if !proto_dir.exists() {
        eprintln!("Proto directory does not exist: {:?}", proto_dir);
        // 跳过 proto 编译，使用已生成的文件
        return Ok(());
    }

    // 检查 protoc 是否可用
    let has_protoc = std::env::var("PROTOC").is_ok() 
        || std::process::Command::new("protoc").arg("--version").output().is_ok();

    if !has_protoc {
        eprintln!("protoc not found, skipping proto compilation");
        // 跳过 proto 编译，使用已生成的文件
        return Ok(());
    }

    // 编译 proto 文件
    if let Err(e) = tonic_build::compile_protos("../proto/runtime.proto") {
        eprintln!("Failed to compile protos: {}", e);
        // 不失败，使用已生成的文件
    }

    Ok(())
}
