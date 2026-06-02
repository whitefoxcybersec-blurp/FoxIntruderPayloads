from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator
import random


class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.registerIntruderPayloadGeneratorFactory(self)
        return

    def getGeneratorName(self):
        return "BHP Payload Generator Modificado"

    def createNewInstance(self, attack):
        return BHPFuzzer(self, attack)


class BHPFuzzer(IIntruderPayloadGenerator):
    def __init__(self, extender, attack):
        self._extender = extender
        self._helpers = extender._helpers
        self._attack = attack
        self.max_payloads = 10
        self._num_iterations = 0

    def hasMorePayloads(self):
        return self._num_iterations < self.max_payloads

    def mutate_payload(self, original_payload):
        if not original_payload:
            original_payload = "test"

        picker = random.randint(1, 3)
        offset = random.randint(0, len(original_payload) - 1)

        # CORREÇÃO: 'back' deve começar de 'offset' até o fim
        front = original_payload[:offset]
        back = original_payload[offset:]

        if picker == 1:
            # CORREÇÃO: operador correto é +=
            front += "'"

        elif picker == 2:
            front += "<script>alert('BHP!');</script>"

        elif picker == 3:
            # CORREÇÃO: definindo variáveis que faltavam
            repeater = random.randint(1, 4)
            chunk_length = random.randint(1, max(1, len(back)))

            for _ in range(repeater):
                front += original_payload[offset: offset + chunk_length]

        return front + back

    def getNextPayload(self, baseValue):
        self._num_iterations += 1

        # CORREÇÃO: Convertendo o array de bytes do Java (baseValue) para string Python
        if baseValue:
            payload_str = "".join(chr(x & 0xFF) for x in baseValue)
        else:
            payload_str = ""

        # Modifica a string
        mutated = self.mutate_payload(payload_str)

        # Retorna o payload modificado (o Jython aceita strings comuns aqui)
        return mutated

    def reset(self):
        self._num_iterations = 0
        return