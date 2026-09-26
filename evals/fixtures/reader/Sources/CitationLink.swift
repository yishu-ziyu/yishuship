import PDFKit

enum CitationLink {
    /// Jumps to the top of the cited page. Citations without a page number do nothing.
    static func open(_ citation: Citation, in view: PDFView) {
        guard let page = citation.page, let target = view.document?.page(at: page - 1) else { return }
        view.go(to: target)
    }
}
