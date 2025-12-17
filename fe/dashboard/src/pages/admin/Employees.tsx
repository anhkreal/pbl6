import AdminLayout from '../../layouts/AdminLayout';
import AdminPinModal from '../../components/AdminPinModal';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEmployees, Employee, shiftEmployeeByUsername, resignEmployeeByUsername, addUserAndAccount } from '../../api/employees';
import { verifyPin } from '../../api/pin';
import ErrorBanner from '../../components/ErrorBanner';

export default function Employees(){
  const [q,setQ]=useState('');
  const [employees,setEmployees]=useState<Employee[]>([]);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [modalAction,setModalAction]=useState<{type:'shift'|'delete'|'add',id:number,username?:string}|null>(null);
  const [showAdd,setShowAdd]=useState(false);
  const [newEmp,setNewEmp]=useState<{name:string,username:string,age:string,address:string,phone:string,shift:'day'|'night'}>({name:'',username:'',age:'',address:'',phone:'',shift:'day'});

  const list=employees;
  const navigate = useNavigate();

  const [refresh, setRefresh] = useState(0);
  useEffect(()=>{
    let ignore=false;
    (async()=>{
      setLoading(true); setError('');
      try{
        const data = await fetchEmployees(q || undefined);
        if(!ignore) setEmployees(data);
      }catch(e:any){ setError(e.message); }finally{ if(!ignore) setLoading(false); }
    })();
    return ()=>{ignore=true;}
  },[q, refresh]);

  const performAction = async (pin: string) => {
    if(!modalAction) return;
    const trimmed = String(pin ?? '').trim();
    console.debug('[Employees] performAction pin raw:', pin, 'trimmed:', trimmed);
    const ok = await verifyPin(trimmed);
    if(!ok){ alert('PIN sai'); return; }
    if(modalAction.type==='shift' && modalAction.username) {
      const emp = employees.find(x => x.username === modalAction.username);
      if (!emp) { alert('Không tìm thấy nhân viên!'); return; }
      await shiftEmployeeByUsername(modalAction.username, emp.shift);
      alert('Đã đổi ca thành công!');
    }
    if(modalAction.type==='delete' && modalAction.username) {
      await resignEmployeeByUsername(modalAction.username);
      setEmployees(e=>e.filter(x=>x.username!==modalAction.username));
      alert('Đã cho nghỉ việc!');
    }
    // 'reset' action removed (no backend endpoint). Use edit-checklog endpoints where applicable.
    if(modalAction.type==='add'){
      if (!newEmp.username.trim()) {
        alert('Username là bắt buộc!');
        return;
      }
      await addUserAndAccount({
        username: newEmp.username.trim(),
        full_name: newEmp.name?.trim() || undefined,
        age: newEmp.age?.trim() ? Number(newEmp.age) : undefined,
        address: newEmp.address?.trim() || undefined,
        phone: newEmp.phone?.trim() || undefined,
        shift: newEmp.shift || 'day',
      });
      const data=await fetchEmployees(); setEmployees(data);
    }
    setModalAction(null); setShowAdd(false);
  };

  return (
    <AdminLayout>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:18}}>
        <h1 style={{margin:0}}>Nhân viên</h1>
        <button className="btn btn-primary" onClick={()=>{setShowAdd(true);setNewEmp({name:'',username:'',age:'',address:'',phone:'',shift:'day'});}}>+ Thêm nhân viên mới</button>
      </div>
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="card-body">
          <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Tìm tên hoặc nhập ID để xem chi tiết" />
        </div>
      </div>
      {loading && <div className="card-body">Đang tải...</div>}
      {error && <div className="card-body"><ErrorBanner message={error} onRetry={()=>setRefresh(v=>v+1)} /></div>}
      <div className="card" style={{overflowX:'auto'}}>
        <table className="table">
          <thead>
            <tr>
              <th>STT</th>
              <th>Avatar</th>
              <th>Tên</th>
              <th>Ca</th>
              <th>Trạng thái</th>
              <th>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {list.map((e,i)=>(
              <tr key={e.id}>
                <td>{i+1}</td>
                <td>
                  {e.avatar_base64
                    ? (
                        <img
                          src={
                            e.avatar_base64.startsWith('data:image')
                              ? e.avatar_base64
                              : `data:image/png;base64,${e.avatar_base64}`
                          }
                          style={{ width: 40, height: 40, borderRadius: 4 }}
                        />
                      )
                    : <div style={{ width: 40, height: 40, background: '#ecf0f1', borderRadius: 4 }} />}
                </td>
                <td><button className="btn btn-ghost" onClick={() => navigate('/admin/employeedetail?username=' + encodeURIComponent(String(e.username)))}>{e.fullName}</button></td>
                <td>{e.shift==='day'?'Ngày':'Đêm'}</td>
                <td><span className={e.status==='working'?'badge badge-success':'badge'}>{e.status==='working'?'Đang làm':'Đã nghỉ'}</span></td>
                <td>
                  <button className="btn btn-ghost" onClick={()=>setModalAction({type:'shift',id:e.id,username:e.username})} style={{marginRight:8}}>Đổi ca</button>
                  <button className="btn btn-ghost" onClick={()=>setModalAction({type:'delete',id:e.id,username:e.username})} style={{color:'#e74c3c', borderColor:'#e74c3c'}}>Nghỉ việc</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {showAdd && (
        <div style={{position:'fixed',top:0,left:0,right:0,bottom:0,background:'rgba(0,0,0,0.2)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center'}}>
          <div className="card" style={{padding:32,minWidth:340}}>
            <div className="card-body">
            <h2 style={{marginTop:0}}>Thêm nhân viên mới</h2>
            <div style={{marginBottom:12}}>
              <input value={newEmp.name} onChange={e=>setNewEmp({...newEmp,name:e.target.value})} placeholder="Họ tên" style={{width:'100%',marginBottom:8}}/>
              <input value={newEmp.username} onChange={e=>setNewEmp({...newEmp,username:e.target.value})} placeholder="Username" style={{width:'100%',marginBottom:8}}/>
              <input value={newEmp.age} onChange={e=>setNewEmp({...newEmp,age:e.target.value})} placeholder="Tuổi" type="number" style={{width:'100%',marginBottom:8}}/>
              <input value={newEmp.address} onChange={e=>setNewEmp({...newEmp,address:e.target.value})} placeholder="Địa chỉ" style={{width:'100%',marginBottom:8}}/>
              <input value={newEmp.phone} onChange={e=>setNewEmp({...newEmp,phone:e.target.value})} placeholder="Số điện thoại" style={{width:'100%',marginBottom:8}}/>
              <select value={newEmp.shift} onChange={e=>setNewEmp({...newEmp,shift:e.target.value as 'day'|'night'})} style={{width:'100%',marginBottom:8}}>
                <option value="day">Ca ngày</option>
                <option value="night">Ca đêm</option>
              </select>
              <input value="123456" disabled style={{width:'100%',marginBottom:8,background:'#f5f5f5'}} placeholder="Mật khẩu mặc định"/>
            </div>
            <div style={{display:'flex',justifyContent:'flex-end',gap:8}}>
              <button className="btn btn-ghost" onClick={()=>setShowAdd(false)}>Hủy</button>
              <button
                onClick={async()=>{
                  if (!newEmp.username.trim()) {
                    alert('Username là bắt buộc!');
                    return;
                  }
                  try {
                    const res = await addUserAndAccount({
                      username: newEmp.username.trim(),
                      full_name: newEmp.name?.trim() || undefined,
                      age: newEmp.age?.trim() ? Number(newEmp.age) : undefined,
                      address: newEmp.address?.trim() || undefined,
                      phone: newEmp.phone?.trim() || undefined,
                      shift: newEmp.shift || 'day',
                    });
                    if (res?.success === false) {
                      alert(res?.message || 'Có lỗi xảy ra khi thêm nhân viên!');
                      return;
                    }
                    alert('Thêm nhân viên thành công!');
                    setShowAdd(false);
                    const data = await fetchEmployees();
                    setEmployees(data);
                  } catch (e: any) {
                    alert(e?.message || 'Có lỗi xảy ra khi thêm nhân viên!');
                  }
                }}
                className="btn btn-primary"
              >Thêm</button>
            </div>
            </div>
          </div>
        </div>
      )}
      <AdminPinModal
        open={modalAction !== null && modalAction.type !== 'add'}
        title="Xác nhận thao tác"
        onConfirm={performAction}
        onCancel={() => setModalAction(null)}
      />
    </AdminLayout>
  );
}
const th:React.CSSProperties={padding:10,fontSize:12,textTransform:'uppercase',color:'#7f8c8d',textAlign:'left'};
const td:React.CSSProperties={padding:10,fontSize:14};