import AdminLayout from '../../layouts/AdminLayout';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEmployees, shiftEmployee, resetEmployee, deleteEmployee, createEmployee, Employee } from '../../api/employees';
import { verifyPin } from '../../api/pin';

export default function Employees(){
  const [q,setQ]=useState('');
  const [employees,setEmployees]=useState<Employee[]>([]);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [modalAction,setModalAction]=useState<{type:'shift'|'reset'|'delete'|'add',id:number}|null>(null);
  const [showAdd,setShowAdd]=useState(false);
  const [pinValue,setPinValue]=useState('');
  const [newEmp,setNewEmp]=useState<{name:string,age:string,address:string,phone:string,shift:'day'|'night'}>({name:'',age:'',address:'',phone:'',shift:'day'});

  const list=employees;
  const navigate = useNavigate();

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
  },[q]);

  const performAction = async () => {
    if(!modalAction) return;
    const trimmed = String(pinValue ?? '').trim();
    console.debug('[Employees] performAction pin raw:', pinValue, 'trimmed:', trimmed);
    const ok = await verifyPin(trimmed);
    if(!ok){ alert('PIN sai'); return; }
    if(modalAction.type==='shift') await shiftEmployee(modalAction.id);
    if(modalAction.type==='reset') await resetEmployee(modalAction.id);
    if(modalAction.type==='delete') { await deleteEmployee(modalAction.id); setEmployees(e=>e.filter(x=>x.id!==modalAction.id)); }
    if(modalAction.type==='add'){
      await createEmployee({ fullName:newEmp.name, age:Number(newEmp.age||0), address:newEmp.address, phone:newEmp.phone, shift:newEmp.shift });
      const data=await fetchEmployees(); setEmployees(data);
    }
    setModalAction(null); setShowAdd(false); setPinValue('');
  };

  return (
    <AdminLayout>
      <h1 style={{marginBottom:18}}>Nhân viên</h1>
      <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Tìm tên hoặc nhập ID để xem chi tiết" style={{padding:8,border:'1px solid #ccc',borderRadius:4,marginBottom:14}}/>
      {loading && <div style={{padding:10}}>Đang tải...</div>}
      {error && <div style={{padding:10,color:'red'}}>{error}</div>}
      <div style={{background:'#fff',borderRadius:8,overflowX:'auto'}}>
        <table style={{width:'100%',borderCollapse:'collapse'}}>
          <thead>
            <tr style={{background:'#f5f5f5'}}>
              <th style={th}>STT</th>
              <th style={th}>Avatar</th>
              <th style={th}>Tên</th>
              <th style={th}>Ca</th>
              <th style={th}>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {list.map((e,i)=>(
              <tr key={e.id} style={{borderTop:'1px solid #ecf0f1'}}>
                <td style={td}>{i+1}</td>
                <td style={td}>
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
                <td style={td}><button onClick={() => navigate('/admin/employeedetail?username=' + encodeURIComponent(String(e.username)))} style={{ background: 'transparent', border: 'none', padding: 0, color: '#3498db', cursor: 'pointer' }}>{e.fullName}</button></td>
                <td style={td}>{e.shift==='day'?'Ngày':'Đêm'}</td>
                <td style={td}><span style={badge(e.status==='working'?'#2ecc71':'#7f8c8d')}>{e.status==='working'?'Đang làm':'Đã nghỉ'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
const th:React.CSSProperties={padding:10,fontSize:12,textTransform:'uppercase',color:'#7f8c8d',textAlign:'left'};
const td:React.CSSProperties={padding:10,fontSize:14};
const badge=(bg:string):React.CSSProperties=>({background:bg,color:'#fff',padding:'4px 8px',borderRadius:4,fontSize:12});