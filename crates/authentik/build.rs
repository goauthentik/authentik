fn main() {
    shadow_rs::ShadowBuilder::builder()
        .deny_const(Default::default())
        .build()
        .unwrap();
}
