import SwiftUI

struct QAPanel: View {
    @State private var question = ""
    @State private var answers: [Answer] = []

    var body: some View {
        VStack(alignment: .leading) {
            ScrollView {
                ForEach(answers) { answer in
                    Text(answer.text)  // plain text: Markdown is not rendered
                }
            }
            TextField("问这本书", text: $question)
                .onSubmit { Task { await ask() } }
        }
    }

    func ask() async {
        let answer = await QAClient.shared.ask(question)
        answers.append(answer)
        question = ""
    }
}
