use tauri::webview::{NewWindowResponse, Url, WebviewWindowBuilder};
use tauri::WebviewUrl;

const APP_HOST: &str = "monitor.goreecloud.com";
const APP_URL: &str = "https://monitor.goreecloud.com";

fn is_allowed_navigation(url: &Url) -> bool {
    if url.as_str() == "about:blank" {
        return true;
    }

    url.scheme() == "https"
        && url.host_str() == Some(APP_HOST)
        && url.port_or_known_default() == Some(443)
        && url.username().is_empty()
        && url.password().is_none()
}

fn navigation_log_fields(url: &Url) -> (&str, &str) {
    (url.scheme(), url.host_str().unwrap_or("none"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let app_url = APP_URL.parse()?;

            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(app_url))
                .title("GoreeCloud Monitor")
                .inner_size(1240.0, 820.0)
                .min_inner_size(360.0, 640.0)
                .on_navigation(|url| {
                    let allowed = is_allowed_navigation(url);
                    if !allowed {
                        let (scheme, host) = navigation_log_fields(url);
                        eprintln!("wardveil_security event=navigation_denied scheme={scheme} host={host}");
                    }
                    allowed
                })
                .on_new_window(|_, _| NewWindowResponse::Deny)
                .build()?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run GoreeCloud Monitor client");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn allows_only_the_canonical_monitor_https_origin() {
        assert!(is_allowed_navigation(&Url::parse("https://monitor.goreecloud.com/").unwrap()));
        assert!(is_allowed_navigation(&Url::parse("https://monitor.goreecloud.com/incidents/").unwrap()));
        assert!(is_allowed_navigation(&Url::parse("about:blank").unwrap()));

        assert!(!is_allowed_navigation(&Url::parse("http://monitor.goreecloud.com/").unwrap()));
        assert!(!is_allowed_navigation(&Url::parse("https://monitor.goreecloud.com:444/").unwrap()));
        assert!(!is_allowed_navigation(&Url::parse("https://example.com/").unwrap()));
        assert!(!is_allowed_navigation(&Url::parse("https://monitor.goreecloud.com.evil.example/").unwrap()));
        assert!(!is_allowed_navigation(&Url::parse("https://user:secret@monitor.goreecloud.com/").unwrap()));
    }

    #[test]
    fn denied_navigation_logging_excludes_path_query_and_fragment() {
        let url = Url::parse("https://example.com/private/path?token=secret#fragment").unwrap();
        let fields = navigation_log_fields(&url);
        assert_eq!(fields, ("https", "example.com"));
        assert!(!fields.0.contains("secret"));
        assert!(!fields.1.contains("secret"));
    }
}
