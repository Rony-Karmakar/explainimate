import { supabase } from './supabaseClient'

export default function LoginPage() {
    const handleGoogleLogin = async () => {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: window.location.origin // returns user here after OAuth
            }
        })
        if (error) console.error('Login error:', error.message)
    }

    return (
        <div>
            <h1>Welcome</h1>
            <button onClick={handleGoogleLogin}>
                Sign in with Google
            </button>
        </div>
    )
}