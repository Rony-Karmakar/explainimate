import { supabase } from './supabaseClient'
import { useAuth } from './AuthContext'

export default function Dashboard() {
    const { session } = useAuth()

    const fetchProtectedData = async () => {
        const token = session.access_token

        const res = await fetch('http://localhost:8000/protected', {
            headers: {
                Authorization: `Bearer ${token}`
            }
        })
        const data = await res.json()
        console.log(data)
    }

    const handleLogout = () => supabase.auth.signOut()

    return (
        <div>
            <p>Logged in as: {session.user.email}</p>
            <button onClick={fetchProtectedData}>Fetch Protected Data</button>
            <button onClick={handleLogout}>Logout</button>
        </div>
    )
}