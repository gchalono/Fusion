"""FNXC:OfflineFinal 2026-11-09-05:40:
Export a child-only seccomp filter with the installed libseccomp. No host policy
is changed. Deny namespace/mount/inspection syscalls; preserve ordinary fork and
threads. clone3 reports ENOSYS so libc uses the filtered clone fallback.
"""
import ctypes
import ctypes.util
import errno
import os
import stat
from functools import lru_cache
from pathlib import Path

DENIED=('unshare','setns','mount','umount2','pivot_root','chroot','ptrace',
        'process_vm_readv','process_vm_writev','fsopen','fsconfig','fsmount',
        'move_mount','open_tree','mount_setattr','bpf','userfaultfd',
        'io_uring_setup','io_uring_enter','io_uring_register','kexec_load',
        'init_module','finit_module','delete_module','reboot','swapon','swapoff',
        'capset','setuid','setgid','setreuid','setregid','setresuid','setresgid','setfsuid','setfsgid')
NAMESPACE_BITS=(0x80,0x20000,0x2000000,0x4000000,0x8000000,0x10000000,0x20000000,0x40000000)

class ArgCompare(ctypes.Structure):
    _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_int),('a',ctypes.c_uint64),('b',ctypes.c_uint64)]


def export_filter(file):
    library=ctypes.util.find_library('seccomp')
    if not library:raise RuntimeError('libseccomp_required')
    lib=ctypes.CDLL(library)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_release.argtypes=[ctypes.c_void_p]
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(ArgCompare)]
    lib.seccomp_export_bpf.argtypes=[ctypes.c_void_p,ctypes.c_int]
    context=lib.seccomp_init(0x7fff0000)
    if not context:raise RuntimeError('seccomp_init_failed')
    def rule(name, error, comparison=None):
        syscall=lib.seccomp_syscall_resolve_name(name.encode())
        if syscall<0:return
        pointer=ctypes.pointer(comparison) if comparison is not None else None
        if lib.seccomp_rule_add_array(context,0x50000|error,syscall,int(comparison is not None),pointer)!=0:
            raise RuntimeError('seccomp_rule_failed:'+name)
    try:
        for name in DENIED:rule(name,errno.EPERM)
        rule('clone3',errno.ENOSYS)
        # FNXC:OfflineFinal 2026-11-09-05:40: No packet/netlink/vsock or other
        # socket families; only Unix and IP sockets confined by the net namespace.
        for family in (0,3,4,5,6,7,8,9):rule('socket',errno.EPERM,ArgCompare(0,4,family,0))
        rule('socket',errno.EPERM,ArgCompare(0,6,10,0))
        rule('socketpair',errno.EPERM,ArgCompare(0,1,1,0))
        for name,arg in (('chmod',1),('fchmod',1),('fchmodat',2),('fchmodat2',2)):
            for bit in (0o4000,0o2000):rule(name,errno.EPERM,ArgCompare(arg,7,bit,bit))
        for bit in NAMESPACE_BITS:rule('clone',errno.EPERM,ArgCompare(0,7,bit,bit))
        if lib.seccomp_export_bpf(context,file.fileno())!=0:raise RuntimeError('seccomp_export_failed')
        file.flush();file.seek(0)
    finally:lib.seccomp_release(context)


@lru_cache(maxsize=1)
def privileged_binaries():
    # FNXC:OfflineFinal 2026-11-09-05:40: Mask setuid/setgid files in the view;
    # never chmod the installed files. /bin is a separately bound alias.
    paths=set()
    for base in ('/usr',):
        for folder,dirs,files in os.walk(base,followlinks=False):
            for name in files:
                path=Path(folder)/name
                if path.is_symlink():continue
                try:info=path.stat()
                except OSError:continue
                if stat.S_ISREG(info.st_mode) and info.st_mode & (stat.S_ISUID|stat.S_ISGID):
                    paths.add(str(path))
                    for original,alias in (('/usr/bin/','/bin/'),('/usr/lib/','/lib/'),('/usr/lib64/','/lib64/')):
                        if str(path).startswith(original):paths.add(str(path).replace(original,alias,1))
    return sorted(paths)
